# objc_method_resolver.py — Phase 16 helper
# Резолвит ObjC-методы CommCenter Mach-O: class_ro_t.baseMethods ->
# relative method_list -> {selname via selref chained-ptr, IMP}.
# Использование: python objc_method_resolver.py <CommCenter.bin> > methods.txt
import struct, sys

def build(fn):
    b = open(fn, 'rb').read()
    ncmds = struct.unpack_from('<I', b, 16)[0]
    off = 32; segs = {}; sects = {}
    for i in range(ncmds):
        cmd, csz = struct.unpack_from('<II', b, off)
        if cmd == 0x19:  # LC_SEGMENT_64
            nm = b[off+8:off+24].split(b'\0')[0].decode()
            va, vs, fo, fs, mx, mi, ns, fl = struct.unpack_from('<QQQQIIII', b, off+24)
            segs[nm] = (va, vs, fo, fs)
            so = off + 72
            for s in range(ns):
                sname = b[so:so+16].split(b'\0')[0].decode()
                seg = b[so+16:so+32].split(b'\0')[0].decode()
                a, ssz = struct.unpack_from('<QQ', b, so+32)
                f0 = struct.unpack_from('<I', b, so+48)[0]
                sects[(seg, sname)] = (a, ssz, f0)
                so += 80
        off += csz
    return b, segs, sects

def run(fn):
    b, segs, sects = build(fn)
    def vm2off(v):
        for nm, (va, vs, fo, fs) in segs.items():
            if va <= v < va+vs:
                return fo + (v-va)
    def dec(raw):
        return 0x100000000 + (raw & 0xffffffff)  # chained fixup: low32 + image base
    def cstr(v):
        o = vm2off(v)
        return b[o:b.find(b'\0', o)] if o is not None else None
    a, ssz, f0 = sects[('__DATA_CONST', '__objc_classlist')]
    res = {}
    for i in range(0, ssz, 8):
        cls = dec(struct.unpack_from('<Q', b, f0+i)[0])
        o = vm2off(cls)
        if o is None:
            continue
        ro = dec(struct.unpack_from('<Q', b, o+32)[0])
        ro_o = vm2off(ro)
        if ro_o is None:
            continue
        cname = cstr(dec(struct.unpack_from('<Q', b, ro_o+24)[0])) or b'?'
        for bmf in (32, 40):  # baseMethods / meta baseMethods
            bm = dec(struct.unpack_from('<Q', b, ro_o+bmf)[0])
            bm_o = vm2off(bm)
            if bm_o is None:
                continue
            flags, cnt = struct.unpack_from('<II', b, bm_o)
            if not (0 < cnt < 6000):
                continue
            for j in range(cnt):
                e = bm_o + 8 + j*12
                if e+12 > len(b):
                    break
                no, ty, im = struct.unpack_from('<iii', b, e)
                sel_slot = e + no
                try:
                    selname = cstr(dec(struct.unpack_from('<Q', b, sel_slot)[0]))
                except Exception:
                    selname = None
                if selname is None:
                    continue
                imp_addr = e + 8 + im
                imp_vm = None
                for nm, (va, vs, fo2, fs) in segs.items():
                    if fo2 <= imp_addr < fo2+fs:
                        imp_vm = va + (imp_addr - fo2)
                res.setdefault(cname.decode('utf8', 'replace'), {})[selname.decode('utf8', 'replace')] = imp_vm
    for cn in sorted(res):
        print('== %s ==' % cn)
        for sn in sorted(res[cn]):
            print('  %s\t0x%x' % (sn, res[cn][sn] or 0))

if __name__ == '__main__':
    run(sys.argv[1])
