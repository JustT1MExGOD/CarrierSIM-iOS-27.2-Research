#!/usr/bin/env python3
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
    segments = []
    cmdoff = 0
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', commands, cmdoff)
        if cmd == 0x19 and cmdsize >= 0x48:
            segname = commands[cmdoff + 8:cmdoff + 24].rstrip(b'\0').decode('ascii', 'replace')
            vmaddr, vmsize, fileoff, filesize = struct.unpack_from('<QQQQ', commands, cmdoff + 24)
            segments.append((segname, vmaddr, vmsize, fileoff, filesize))
        cmdoff += cmdsize
    if not segments:
        print(f'{name}: no 64-bit segments')
        return
    max_file = max(fo + fs for _, _, _, fo, fs in segments)
    out = bytearray(max_file)
    # Preserve header and load commands exactly as present at the image start.
    with open(fn, 'rb') as f:
        f.seek(off)
        prefix = f.read(min(max_file, 0x20 + sizeofcmds))
    out[:len(prefix)] = prefix
    missing = []
    copied = []
    for segname, vmaddr, vmsize, fileoff, filesize in segments:
        if filesize == 0: continue
        srcfn, srcoff = locate(vmaddr, filesize)
        if not srcfn:
            missing.append((segname, vmaddr, filesize))
            continue
        with open(srcfn, 'rb') as sf:
            sf.seek(srcoff)
            data = sf.read(filesize)
        out[fileoff:fileoff + len(data)] = data
        if len(data) != filesize:
            missing.append((segname, vmaddr, filesize - len(data)))
        else:
            copied.append((segname, srcfn, srcoff, filesize))
    path = os.path.join(OUT_DIR, name + '_B2.dylib')
    with open(path, 'wb') as f: f.write(out)
    print(f'{name}: wrote={len(out)} bytes; missing={len(missing)}; path={path}')
    for segname, srcfn, srcoff, size in copied:
        print(f'  copied {segname} {size} from {os.path.basename(srcfn)}+0x{srcoff:x}')
    for segname, vmaddr, size in missing:
        print(f'  MISSING {segname} vm=0x{vmaddr:x} size=0x{size:x}')

for name, va in TARGETS.items():
    extract(name, va)
