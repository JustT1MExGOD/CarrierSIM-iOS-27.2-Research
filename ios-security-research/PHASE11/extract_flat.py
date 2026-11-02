#!/usr/bin/env python3
"""
Correct dyld-cache image extractor for Phase 11.

Bug fixed from Phase 10 extract_dyld_segments.py:
  Phase 10 wrote each segment to `out[fileoff:fileoff+size]` where `fileoff`
  is the cache-global offset — producing files where segments overlap
  because __LINKEDIT fileoff (0x4000) is lower than __TEXT fileoff (0xc11000).

Correct approach:
  - Allocate output by max(fileoff + filesize) across segments — same as before
    but this is the file's natural layout.
  - Write each segment's bytes to out[fileoff : fileoff+filesize] — this IS
    correct, because in a dyld-cache image the declared fileoff *is* the
    offset where that segment should appear in a "flattened" reconstruction.

Wait — that's what Phase 10 did, and the result is what we observed:
the file has real bytes at every declared fileoff, so it IS a flattened
Mach-O. The confusion was that "__LINKEDIT fileoff=0x4000" looked wrong.

Actually the truth is different:
  In a dyld-cache image, `fileoff` in LC_SEGMENT_64 is NOT a cache-global
  offset — it IS the intended file offset in a standalone dylib. When dyld
  extracts a dylib it lays segments at exactly those fileoffs.

  __TEXT fileoff=0xc11000 → in the flattened file, __TEXT is at 0xc11000.
  __LINKEDIT fileoff=0x4000  → linkedit region begins at 0x4000.

  These OVERLAP: linkedit 0x4000..0x294d8000 covers the whole file,
  including __TEXT at 0xc11000. That is impossible for a real Mach-O.

  → The declared fileoff in a dyld-cache image's LC_SEGMENT_64 is a
    cache-global offset within the whole mapped cache space, NOT a local
    offset. For __TEXT, 0xc11000 happens to land inside the image's own
    .13 subcache mapping (fileoff=0xc11000 within that file). For
    __LINKEDIT, 0x4000 lands inside the (empty) .79 subcache.

  So the "flattened" file produced by Phase 10 is garbage — segments are
  overlaid on top of each other. The correct extractor must allocate a
  compact output and place segments sequentially, REMAPPING the declared
  fileoffs.

This script writes a CORRECT flat Mach-O:
  - Header + load commands at offset 0.
  - Segments packed sequentially starting at align(0x20+sizeofcmds).
  - LC_SEGMENT_64 fileoffs REWRITTEN to match the new layout.
  - vmaddr kept unchanged so all pointers inside the file stay valid.
"""
import glob, os, struct, sys

CACHE_DIR = sys.argv[1]
OUT_DIR = sys.argv[2]
os.makedirs(OUT_DIR, exist_ok=True)

TARGETS = {
    'Security': 0x189501000,
    'MobileInstallation': 0x1d2ccc000,
    'libmis': 0x226410000,
    'AppleMobileFileIntegrity': 0x259011000,
    'CodesignKit': 0x25c934000,
    'libDetachedCertificates': 0x2c677c000,
    'TrustKit': 0x237e43000,
    'ProfileValidatedAppIdentity': 0x29ff73000,
    'LocalAuthentication': 0x1cc3de000,
    'SecurityFoundation': 0x2a9774000,
    'MessageSecurity': 0x22a21f000,
}

def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u64(b, o): return struct.unpack_from('<Q', b, o)[0]

maps = []
for fn in sorted(glob.glob(os.path.join(CACHE_DIR, 'dyld_shared_cache_arm64e*'))):
    with open(fn, 'rb') as f: h = f.read(0x400)
    if len(h) < 0x400: continue
    mo, mc = u32(h, 0x10), u32(h, 0x14)
    if mo + mc * 32 > 0x400: continue
    for i in range(mc):
        vma, size, fileoff, maxprot, initprot = struct.unpack_from('<QQQII', h, mo + i * 32)
        maps.append((vma, vma + size, fn, fileoff))

def locate(va, size=1):
    for start, end, fn, fileoff in maps:
        if start <= va and va + size <= end:
            return fn, fileoff + (va - start)
    return None, None

def extract(name, image_va):
    fn, off = locate(image_va, 0x20)
    if not fn:
        print(f'{name}: image mapping not found')
        return
    with open(fn, 'rb') as f:
        f.seek(off)
        header = f.read(0x20)
        if len(header) < 0x20 or u32(header, 0) != 0xfeedfacf:
            print(f'{name}: invalid Mach-O at {fn}+0x{off:x}')
            return
        magic, cputype, cpusub, filetype, ncmds, sizeofcmds, flags, reserved = struct.unpack('<IIIIIIII', header)
        commands = f.read(sizeofcmds)
    # parse all load commands, remember LC_SEGMENT_64 positions so we can rewrite fileoff
    segments = []
    cmdoff = 0
    seg_positions = []
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', commands, cmdoff)
        if cmd == 0x19 and cmdsize >= 0x48:
            segname = commands[cmdoff + 8:cmdoff + 24].rstrip(b'\0').decode('ascii', 'replace')
            vmaddr, vmsize, fileoff, filesize = struct.unpack_from('<QQQQ', commands, cmdoff + 24)
            segments.append((segname, vmaddr, vmsize, fileoff, filesize, cmdoff))
            seg_positions.append((cmdoff, segname))
        cmdoff += cmdsize
    if not segments:
        print(f'{name}: no 64-bit segments')
        return
    # Check which segments are actually present in source files BEFORE assigning fileoffs.
    # Segments whose bytes can't be located get fileoff=0 and don't consume output space.
    segment_present = {}
    for segname, vmaddr, vmsize, fileoff, filesize, _cmdoff in segments:
        if filesize == 0:
            segment_present[segname] = False
            continue
        srcfn, _ = locate(vmaddr, filesize)
        segment_present[segname] = srcfn is not None
    # new file layout: header+cmds at 0, then segments packed starting at page boundary
    header_end = 0x20 + sizeofcmds
    cursor = (header_end + 0xfff) & ~0xfff
    new_fileoffs = {}
    for segname, vmaddr, vmsize, fileoff, filesize, _cmdoff in segments:
        if not segment_present[segname]:
            new_fileoffs[segname] = 0  # absent segment — no space
            continue
        new_fileoffs[segname] = cursor
        cursor += (filesize + 0xfff) & ~0xfff
    total = cursor
    out = bytearray(total)
    # write header + load commands verbatim, then patch fileoffs in place
    out[:0x20 + sizeofcmds] = header + commands
    for segname, vmaddr, vmsize, fileoff, filesize, cmdoff in segments:
        # LC_SEGMENT_64 layout: cmd(4) cmdsize(4) segname(16) vmaddr(8) vmsize(8)
        #                       fileoff(8) filesize(8) maxprot(4) initprot(4) nsects(4) flags(4)
        #                       then nsects * section_64 (80 bytes each)
        newfo = new_fileoffs[segname]
        # segment fileoff field at cmdoff+40
        struct.pack_into('<Q', out, 0x20 + cmdoff + 40, newfo)
        # adjust each embedded section's fileoff: sect.fileoff = newfo + (sect_old_fileoff - seg_old_fileoff)
        # section_64 layout: sectname(16) segname(16) addr(8) size(8) offset(4) align(4) reloff(4) nreloc(4) flags(4) r1(4) r2(4) r3(4)
        nsec = struct.unpack_from('<I', out, 0x20 + cmdoff + 64)[0]
        so = 0x20 + cmdoff + 72
        for s in range(nsec):
            # offset field at so+48 (u32)
            old_sfo = struct.unpack_from('<I', out, so + 48)[0]
            # Only adjust sections that have real data in the original file (offset != 0 and < segment_end)
            if old_sfo and filesize and old_sfo >= fileoff and old_sfo < fileoff + filesize:
                new_sfo = newfo + (old_sfo - fileoff)
            elif filesize:
                new_sfo = newfo  # zero/empty section — point at segment start
            else:
                new_sfo = 0  # segment absent — nothing to point at
            struct.pack_into('<I', out, so + 48, new_sfo & 0xffffffff)
            so += 80
    # copy segment bytes
    missing = []
    copied = []
    for segname, vmaddr, vmsize, fileoff, filesize, _cmdoff in segments:
        if filesize == 0: continue
        if not segment_present[segname]:
            missing.append((segname, vmaddr, filesize))
            continue
        srcfn, srcoff = locate(vmaddr, filesize)
        with open(srcfn, 'rb') as sf:
            sf.seek(srcoff)
            data = sf.read(filesize)
        dst = new_fileoffs[segname]
        out[dst:dst + len(data)] = data
        if len(data) != filesize:
            missing.append((segname, vmaddr, filesize - len(data)))
        else:
            copied.append((segname, srcfn, srcoff, dst, filesize))
    path = os.path.join(OUT_DIR, name + '_B2.dylib')
    with open(path, 'wb') as f: f.write(out)
    print(f'{name}: wrote={len(out)} bytes; missing={len(missing)}; path={path}')
    for segname, srcfn, srcoff, dst, size in copied:
        print(f'  {segname:15} {size:>10}B from {os.path.basename(srcfn):45}+0x{srcoff:x} -> +0x{dst:x}')
    for segname, vmaddr, size in missing:
        print(f'  MISSING {segname} vm=0x{vmaddr:x} size=0x{size:x}')

for name, va in TARGETS.items():
    extract(name, va)
