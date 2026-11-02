# p17_entmap_extractor.py — Phase 17 helper
# Извлекает полную таблицу selector -> entitlement code из
# -[CTXPCService requiredEntitlementForRequest:] в CommCenter.
# Таблица строится серией 16-байтовых записей:
#   adrp x?, selrefs_page
#   ldr  x?, [x?, #off]        ; selref slot -> selname cstring
#   str  x?, [x8, #N]          ; request key (selector ptr)
#   str  w?, [x8, #N+8]        ; entitlement code (imm)
# Использование: python p17_entmap_extractor.py <CommCenter.bin> <func_va> <max_insn>
import struct, sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_MEM, ARM64_OP_IMM, ARM64_REG_X8, ARM64_REG_W8, ARM64_OP_REG

def build(fn):
    b = open(fn, 'rb').read()
    ncmds = struct.unpack_from('<I', b, 16)[0]
    off = 32; segs = {}
    for i in range(ncmds):
        cmd, csz = struct.unpack_from('<II', b, off)
        if cmd == 0x19:  # LC_SEGMENT_64
            nm = b[off+8:off+24].split(b'\0')[0].decode()
            va, vs, fo, fs, mx, mi, ns, fl = struct.unpack_from('<QQQQIIII', b, off+24)
            segs[nm] = (va, vs, fo, fs)
        off += csz
    return b, segs

def vm2off(segs, v):
    for nm, (va, vs, fo, fs) in segs.items():
        if va <= v < va + vs:
            return fo + (v - va)

def dec(raw):
    return 0x100000000 + (raw & 0xffffffff)

def cstr(b, segs, v):
    o = vm2off(segs, v)
    if o is None:
        return None
    e = b.find(b'\0', o)
    return b[o:e].decode('utf8', 'replace')

def extract(fn, fva, maxinsn):
    b, segs = build(fn)
    fo = vm2off(segs, fva)
    code = b[fo:fo + maxinsn * 4]
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    insns = list(md.disasm(code, fva))
    # pass 1: ldr x?,[x?,#imm] where base was set by adrp -> selref slot -> selname
    adrp = {}          # reg -> page addr
    regval = {}        # reg -> resolved selref slot vm
    pending_sel = {}   # reg -> selname
    recs = []          # (disp, selname, code)
    last_str = {}      # disp -> selname for pairing
    for i, in_ in enumerate(insns):
        ops = in_.operands
        if in_.mnemonic == 'adrp' and len(ops) == 2:
            adrp[ops[0].reg] = ops[1].imm
        elif in_.mnemonic == 'ldr' and len(ops) == 2 and ops[1].type == ARM64_OP_MEM:
            base = ops[1].mem.base; disp = ops[1].mem.disp
            if base in adrp:
                slot = adrp[base] + disp
                o = vm2off(segs, slot)
                if o is not None:
                    raw = struct.unpack_from('<Q', b, o)[0]
                    tgt = dec(raw)
                    selname = cstr(b, segs, tgt)
                    if selname:
                        pending_sel[ops[0].reg] = selname
        elif in_.mnemonic == 'str' and len(ops) == 2 and ops[1].type == ARM64_OP_MEM:
            dst = ops[1].mem.base; disp = ops[1].mem.disp
            src = ops[0].reg
            if dst in (ARM64_REG_X8,) or in_.op_str.split(',')[-1].strip().startswith('x8'):
                if src in pending_sel:
                    recs.append([disp, pending_sel[src], None])
                    last_str[disp] = recs[-1]
            # entitlement-code write: str w?,[x8,#N+8]
            opstr = in_.op_str
            if '[x8' in opstr:
                pass
        if in_.mnemonic in ('ret', 'retab') and i > 40:
            # allow trailing cleanup writes; stop at second ret
            rets = sum(1 for x in insns[:i+1] if x.mnemonic in ('ret', 'retab'))
            if rets >= 2:
                break
    # pass 2: pair code writes. For each record (disp, sel), find str w?,[x8,#disp+8]
    # We rescan tracking w-register immediates.
    movw = {}  # reg -> imm
    out = {}
    for i, in_ in enumerate(insns):
        ops = in_.operands
        if in_.mnemonic in ('mov', 'movz', 'movk') and len(ops) == 2 and ops[1].type == ARM64_OP_IMM:
            movw[ops[0].reg] = ops[1].imm if in_.mnemonic != 'movk' else (movw.get(ops[0].reg, 0) | (ops[1].imm << 16))
        elif in_.mnemonic == 'orr' and len(ops) == 3 and ops[2].type == ARM64_OP_IMM:
            movw[ops[0].reg] = ops[1].reg | ops[2].imm if ops[1].type == ARM64_OP_REG else ops[2].imm
        elif in_.mnemonic == 'str' and len(ops) == 2 and ops[1].type == ARM64_OP_MEM:
            opstr = in_.op_str
            if '[x8' not in opstr:
                continue
            disp = ops[1].mem.disp
            # find record at disp-8
            sel = None
            for r in recs:
                if r[0] == disp - 8:
                    sel = r[1]
            if sel:
                src = ops[0].reg
                code = movw.get(src)
                out[sel] = code
    return out

if __name__ == '__main__':
    fn, fva, mx = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
    sys.stdout.reconfigure(encoding='utf8', errors='replace')
    res = extract(fn, fva, mx)
    for k in sorted(res):
        print('%s:\t%s' % (k, res[k]))
    print('# total %d' % len(res), file=sys.stderr)
