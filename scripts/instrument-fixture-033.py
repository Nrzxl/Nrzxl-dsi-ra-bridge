"""Original MIT. Whitelisted fixture-only .nds instrumentation, never an arbitrary ROM patcher."""
import argparse, hashlib, json, math, struct, zlib
from pathlib import Path
BASE, END, STATE, RING = 0x02200000,0x02220000,0x02202000,0x02203000
PUSH=0xE92D4010
def symbols(text):
    out={}
    for line in text.splitlines():
        p=line.split()
        if len(p)>=3:
            try: out[p[-1]]=int(p[0],16)
            except ValueError: pass
    return out
def crc16(b):
    c=0xFFFF
    for v in b:
        c^=v
        for _ in range(8): c=(c>>1)^((c&1)*0xA001)
    return c
def u32(b,o):return struct.unpack_from("<I",b,o)[0]
def word(b,o,v):struct.pack_into("<I",b,o,v)
def overlap(a,n,b,m):return a<b+m and b<a+n
def instrument(original, syms, module, module_syms, sections=None):
    if not (0x200<=len(original)<=4*1024*1024):raise ValueError("fixture size")
    if b"DSI_RA_INDEPENDENT_FIXTURE_033" not in original:raise ValueError("not our independently built fixture")
    if original[0x12] not in (0,2):raise ValueError("unit code")
    if struct.unpack_from("<H",original,0x15e)[0]!=crc16(original[:0x15e]):raise ValueError("header CRC")
    off,entry,ram,size=struct.unpack_from("<4I",original,0x20)
    if not (off>=0x200 and off+size<=len(original) and 0x02000000<=ram<ram+size<=0x02100000):raise ValueError("ARM9 bounds")
    if not (ram<=entry&~1<ram+size):raise ValueError("entry")
    for at in [0x30,0x1c0,0x1d0]:
        if at>=0x1c0 and not original[0x12]&2:continue
        r=u32(original,at+8);n=u32(original,at+12)
        if n and overlap(r,n,BASE,END-BASE):raise ValueError("other CPU/TWL overlaps resident")
    for name in ["__bss_start__","__bss_end__","__heap_start_ntr","__heap_start_twl"]:
        if name in syms and BASE<=syms[name]<END:raise ValueError("startup clear/heap overlaps")
    hook,watch=syms["game_vblank"],syms["game_state"]
    # Modern Calico relocates .main from its header load address to a lower VMA.
    # Patch the verified file LMA, while the branch/resume use the runtime VMA.
    hook_lma=hook
    if "__main_start" in syms and "__main_lma" in syms and syms["__main_start"]<=hook<syms.get("__main_end",0):
        hook_lma=syms["__main_lma"]+hook-syms["__main_start"]
    if sections:
        for sec_size,vma,lma in sections:
            if vma<=hook<hook+4<=vma+sec_size:
                hook_lma=lma+hook-vma;break
    if not (ram<=hook_lma<ram+size-4 and 0x02000000<=watch<=0x02100000-20 and not watch&3):
        raise ValueError("watch/hook bounds: ram=%08x size=%08x hook=%08x lma=%08x watch=%08x"%(ram,size,hook,hook_lma,watch))
    site=off+hook_lma-ram
    if u32(original,site)!=PUSH:raise ValueError("unrelocatable/unknown displaced instruction")
    if not (64<len(module)<=4096 and module[:8]==b"DSIOBS33"):raise ValueError("module bounded header")
    if module_syms["observer_entry"]!=BASE+64:raise ValueError("module entry")
    window=bytearray(END-BASE);window[:len(module)]=module
    word(window,20,watch);word(window,24,hook);word(window,28,hook+4)
    resume=module_syms["observer_resume"]-BASE
    if not 64<=resume<len(module)-3:raise ValueError("trampoline literal")
    word(window,resume,hook+4)
    window[0x1c000:0x20000]=b"\xa5"*0x4000
    delta=(BASE+64)-(hook+8)
    if delta%4 or not -(1<<25)<=delta<(1<<25):raise ValueError("ARM branch reach")
    expanded=bytearray(END-ram)
    expanded[:size]=original[off:off+size]
    word(expanded,hook_lma-ram,0xEA000000|((delta>>2)&0xFFFFFF))
    expanded[BASE-ram:END-ram]=window
    patched=bytearray(original);new_off=(len(patched)+0x1ff)&~0x1ff
    patched.extend(b"\0"*(new_off-len(patched)));patched.extend(expanded)
    word(patched,0x20,new_off);word(patched,0x2c,len(expanded));word(patched,0x80,len(patched))
    patched[0x14]=max(0,(len(patched)-1).bit_length()-17)
    if patched[0x12]&2:word(patched,0x210,len(patched))
    struct.pack_into("<H",patched,0x15e,crc16(patched[:0x15e]))
    # Both CPUs and original entry execute normally; the ARM7/TWL file sections are unchanged.
    evidence=dict(version="0.3.3",original_sha256=hashlib.sha256(original).hexdigest(),
        observed_sha256=hashlib.sha256(patched).hexdigest(),observed_crc32=zlib.crc32(patched),
        observed_bytes=len(patched),arm9_original_entry=entry,arm9_original_size=size,
        arm9_expanded_size=len(expanded),arm9_ram=ram,hook_address=hook,hook_load_address=hook_lma,watch_address=watch,
        displaced_instruction=PUSH,resume_address=hook+4,observer_base=BASE,observer_end=END,
        observer_entry=BASE+64,observer_code_bytes=len(module),records=1200,record_bytes=32,
        arm7_unchanged=True,arm9i_arm7i_unchanged=True,scope="fixture-only external hook; independent full NDS")
    return bytes(patched),evidence
def section_map(text):
    result=[]
    for line in text.splitlines():
        p=line.split()
        if len(p)>=6 and p[0].isdigit() and p[1].startswith("."):
            result.append(tuple(int(x,16) for x in p[2:5]))
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--fixture",type=Path,required=True);p.add_argument("--symbols",type=Path,required=True)
    p.add_argument("--sections",type=Path);p.add_argument("--module",type=Path,required=True);p.add_argument("--module-symbols",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    data,manifest=instrument(a.fixture.read_bytes(),symbols(a.symbols.read_text()),a.module.read_bytes(),symbols(a.module_symbols.read_text()),section_map(a.sections.read_text()) if a.sections else None)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"Fixture_B_033_observed.nds").write_bytes(data)
    (a.output/"instrumentation.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (a.output/"expected.h").write_text("#define LAB_B_BYTES "+str(len(data))+"u\n#define LAB_B_CRC 0x%08Xu\n"%zlib.crc32(data))
    print(json.dumps(manifest))
if __name__=="__main__":main()
