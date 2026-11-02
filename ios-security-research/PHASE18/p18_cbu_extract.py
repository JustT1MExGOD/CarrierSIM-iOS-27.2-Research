# p18_cbu_extract.py — Phase 18 helper
# Извлекает __TEXT сегмент CarrierBundleUtilities.dylib из dyld shared cache.
# Использование: python p18_cbu_extract.py <subcache> <image_va> <out>
import struct, sys, hashlib

def main(subcache, image_va, out):
    f = open(subcache, 'rb')
    hdr = f.read(0x400)
    mapoff, mapcnt = struct.unpack_from('<II', hdr, 0x10)
    f.seek(mapoff)
    fileoff = None
    for i in range(mapcnt):
        addr, size, fo, mi, mx = struct.unpack_from('<QQQII', f.read(32))
        if addr <= image_va < addr + size:
            fileoff = fo + (image_va - addr)
    if fileoff is None:
        sys.exit('image VA not mapped in this subcache')
    f.seek(fileoff)
    mh = f.read(32)
    ncmds = struct.unpack_from('<I', mh, 16)[0]
    f.seek(fileoff)
    seg_data = f.read(0x4000)
    off = 32
    for i in range(ncmds):
        cmd, cs = struct.unpack_from('<II', seg_data, off)
        if cmd == 0x19:
            nm = seg_data[off+8:off+24].split(b'\0')[0]
            va, vs, fo, fs = struct.unpack_from('<QQQQ', seg_data, off+24)
            if nm == b'__TEXT':
                f.seek(fo)
                data = f.read(fs)
                open(out, 'wb').write(data)
                print('__TEXT', hex(va), hex(fs), '->', out)
                print('SHA-256', hashlib.sha256(data).hexdigest())
                return
        off += cs
    sys.exit('__TEXT segment not found')

if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2], 16), sys.argv[3])
