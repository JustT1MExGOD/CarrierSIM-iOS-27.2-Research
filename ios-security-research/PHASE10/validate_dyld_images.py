#!/usr/bin/env python3
import glob, json, os, struct, hashlib, sys
CACHE_DIR = sys.argv[1]
OUT = sys.argv[2]
TARGETS = {
 'Security': ('/System/Library/Frameworks/Security.framework/Security', 0x189501000),
 'MobileInstallation': ('/System/Library/PrivateFrameworks/MobileInstallation.framework/MobileInstallation', 0x1d2ccc000),
 'libmis': ('/usr/lib/libmis.dylib', 0x226410000),
 'AppleMobileFileIntegrity': ('/System/Library/PrivateFrameworks/AppleMobileFileIntegrity.framework/AppleMobileFileIntegrity', 0x259011000),
 'CodesignKit': ('/System/Library/PrivateFrameworks/CodesignKit.framework/CodesignKit', 0x25c934000),
 'libDetachedCertificates': ('/usr/lib/libDetachedCertificates.dylib', 0x2c677c000),
 'TrustKit': ('/System/Library/PrivateFrameworks/TrustKit.framework/TrustKit', 0x237e43000),
 'ProfileValidatedAppIdentity': ('/System/Library/PrivateFrameworks/ProfileValidatedAppIdentity.framework/ProfileValidatedAppIdentity', 0x29ff73000),
 'LocalAuthentication': ('/System/Library/Frameworks/LocalAuthentication.framework/LocalAuthentication', 0x1cc3de000),
 'SecurityFoundation': ('/System/Library/PrivateFrameworks/SecurityFoundation.framework/SecurityFoundation', 0x2a9774000),
 'MessageSecurity': ('/System/Library/PrivateFrameworks/MessageSecurity.framework/MessageSecurity', 0x22a21f000),
}

def read_u32(b,o): return struct.unpack_from('<I',b,o)[0]
def read_u64(b,o): return struct.unpack_from('<Q',b,o)[0]

def cstr(b): return b.split(b'\0',1)[0].decode('utf-8','replace')

maps=[]
for fn in sorted(glob.glob(os.path.join(CACHE_DIR,'dyld_shared_cache_arm64e*'))):
    with open(fn,'rb') as f: h=f.read(0x400)
    if len(h)<0x400: continue
    mo,mc=read_u32(h,0x10),read_u32(h,0x14)
    if mo+mc*32>0x400: continue
    for i in range(mc):
        vma,size,fo,mp,ip=struct.unpack_from('<QQQII',h,mo+i*32)
        maps.append({'start':vma,'end':vma+size,'file':fn,'fileoff':fo})

def locate(addr,n=1):
    for m in maps:
        if m['start']<=addr and addr+n<=m['end']:
            return m['file'],m['fileoff']+addr-m['start']
    return None,None

def read_at(addr,n):
    fn,fo=locate(addr,n)
    if not fn:return None,None
    with open(fn,'rb') as f:
        f.seek(fo); return f.read(n),(fn,fo)

def parse(name,path,va):
    h,loc=read_at(va,0x20)
    item={'name':name,'path':path,'image_vmaddr':hex(va),'source_file':loc[0] if loc else None,'source_offset':hex(loc[1]) if loc else None}
    if not h or len(h)<0x20:
        item['status']='NOT VERIFIED'; item['reason']='header unavailable'; return item
    magic,cputype,cpusub,filetype,ncmds,sizeofcmds,flags,res=struct.unpack('<IIIIIIII',h)
    item.update({'magic':hex(magic),'cpu_type':hex(cputype),'cpu_subtype':hex(cpusub),'filetype':filetype,'ncmds':ncmds,'sizeofcmds':sizeofcmds,'flags':hex(flags)})
    cmds,_=read_at(va+0x20,sizeofcmds)
    if not cmds or len(cmds)<sizeofcmds:
        item['status']='PARTIALLY VERIFIED'; item['reason']='load commands incomplete'; return item
    off=0; segs=[]; dylibs=[]; uuid=None; codesig=None; symtab=None; dyldinfo=None
    for i in range(ncmds):
        if off+8>len(cmds): break
        cmd,cs=struct.unpack_from('<II',cmds,off)
        if cs<8 or off+cs>len(cmds): break
        if cmd==0x19:
            nm=cstr(cmds[off+8:off+24]); vm,vs,fo,fs=struct.unpack_from('<QQQQ',cmds,off+24)
            segs.append({'name':nm,'vmaddr':hex(vm),'vmsize':hex(vs),'fileoff':hex(fo),'filesize':hex(fs)})
        elif cmd==0x1b and cs>=24:
            raw=cmds[off+8:off+24]; uuid='-'.join([raw[0:4].hex(),raw[4:6].hex(),raw[6:8].hex(),raw[8:10].hex(),raw[10:16].hex()]).upper()
        elif cmd in (0xc,0x18,0x80000018) and cs>=24:
            nameoff=read_u32(cmds,off+8)
            if nameoff<cs: dylibs.append(cstr(cmds[off+nameoff:off+cs]))
        elif cmd==0x2 and cs>=24: symtab={'symoff':hex(read_u32(cmds,off+8)),'nsyms':read_u32(cmds,off+12),'stroff':hex(read_u32(cmds,off+16)),'strsize':read_u32(cmds,off+20)}
        elif cmd in (0x22,0x80000022) and cs>=48: dyldinfo={'rebase_off':hex(read_u32(cmds,off+8)),'bind_off':hex(read_u32(cmds,off+16)),'weak_bind_off':hex(read_u32(cmds,off+24)),'lazy_bind_off':hex(read_u32(cmds,off+32)),'export_off':hex(read_u32(cmds,off+40))}
        elif cmd==0x1d and cs>=16: codesig={'dataoff':hex(read_u32(cmds,off+8)),'datasize':hex(read_u32(cmds,off+12))}
        off+=cs
    item.update({'uuid':uuid,'segments':segs,'load_dylibs':dylibs,'symtab':symtab,'dyld_info':dyldinfo,'code_signature':codesig})
    item['has_text']=any(x['name']=='__TEXT' for x in segs); item['has_data']=any(x['name'] in ('__DATA','__DATA_CONST','__AUTH_CONST') for x in segs); item['has_linkedit']=any(x['name']=='__LINKEDIT' for x in segs)
    item['status']='PARTIALLY VERIFIED' if not item['has_linkedit'] else 'VERIFIED'
    item['reason']='Image header, load commands, and mapped segments recovered; shared __LINKEDIT split is empty' if not item['has_linkedit'] else 'header and load commands recovered'
    return item

result={'cache':os.path.join(CACHE_DIR,'dyld_shared_cache_arm64e'),'targets':[]}
for name,(path,va) in TARGETS.items(): result['targets'].append(parse(name,path,va))
with open(OUT,'w',encoding='utf-8') as f: json.dump(result,f,indent=2,ensure_ascii=False)
for x in result['targets']:
 print(x['name'],x.get('status'),x.get('uuid'),x.get('has_linkedit'),len(x.get('load_dylibs',[])))
