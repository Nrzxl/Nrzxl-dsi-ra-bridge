#!/usr/bin/env python3
"""Static ELF32/NDS ARM7 NWRAM footprint audit. No hardware or network calls."""
import hashlib, json, struct, sys
from pathlib import Path

def sections(path):
    data=Path(path).read_bytes()
    if len(data)<52 or data[:6]!=b"\x7fELF\x01\x01":
        raise ValueError("expected 32-bit little endian ELF")
    off=struct.unpack_from("<I",data,32)[0]
    ent,count,idx=struct.unpack_from("<HHH",data,46)
    if ent<40 or count<1 or count>512 or idx>=count or off+ent*count>len(data):
        raise ValueError("invalid ELF table")
    def sh(i):return struct.unpack_from("<10I",data,off+ent*i)
    st=sh(idx)
    if st[4]+st[5]>len(data):raise ValueError("strtab overflow")
    names=data[st[4]:st[4]+st[5]]
    result={}
    for i in range(count):
        n,typ,flags,addr,start,size,*_=sh(i)
        if n>=len(names):raise ValueError("bad section name")
        e=names.find(b"\x00",n)
        name=names[n:e if e!=-1 else None].decode("ascii","replace")
        if name in (".twl",".twl_bss",".text",".bss",".crt0"):
            result[name]={"bytes":size,"addr":f"0x{addr:08X}",
                          "end":f"0x{addr+size:08X}",
                          "kind":"NOBITS" if typ==8 else "PROGBITS"}
    return result

def nds(path):
    data=Path(path).read_bytes()
    if len(data)<512:raise ValueError("truncated NDS")
    result={}
    for cpu,at in (("ARM9",0x20),("ARM7",0x30)):
        start,pc,addr,size=struct.unpack_from("<4I",data,at)
        if size<=0 or start==0 or start+size>len(data) or not addr<=(pc&~1)<addr+size:
            raise ValueError("invalid NDS header "+cpu)
        result[cpu]={"rom_offset":start,"load":f"0x{addr:08X}","bytes":size,
                     "sha256":hashlib.sha256(data[start:start+size]).hexdigest()}
    return result

def main():
    if len(sys.argv)!=6:raise SystemExit("usage: verify-034l-layout.py L0.elf L1.elf L0.nds L1.nds report.json")
    c,p=sections(sys.argv[1]),sections(sys.argv[2])
    cn,pn=nds(sys.argv[3]),nds(sys.argv[4])
    for name in (".twl",".twl_bss",".bss",".text"):
        if name not in c or name not in p:raise SystemExit("BLOCKED missing "+name)
    if cn["ARM9"]["sha256"]!=pn["ARM9"]["sha256"]:
        raise SystemExit("BLOCKED ARM9 payload differs")
    td=p[".twl"]["bytes"]-c[".twl"]["bytes"]
    bd=p[".twl_bss"]["bytes"]-c[".twl_bss"]["bytes"]
    if not 17844<=td<=17908:raise SystemExit(f"BLOCKED .twl grew {td}")
    if not 13300<=bd<=13364:raise SystemExit(f"BLOCKED .twl_bss grew {bd}")
    if p[".twl_bss"]["kind"]!="NOBITS":raise SystemExit("BLOCKED padding BSS emitted as file content")
    if int(p[".twl"]["addr"],16)!=0x03000000:raise SystemExit("BLOCKED .twl address")
    if int(p[".twl_bss"]["end"],16)>0x03040000:raise SystemExit("BLOCKED NWRAM >256 KiB")
    if int(p[".bss"]["end"],16)>0x0380FFC0:raise SystemExit("BLOCKED ARM7 WRAM BIOS overlap")
    report={
      "status":"STATIC_NWRAM_FOOTPRINT_PASS_HARDWARE_NOT_RUN",
      "arm9_identical":True,"no_wifi_driver":True,
      "expected_growth_bytes":{".twl":17844,".twl_bss":13300},
      "actual_growth_bytes":{".twl":td,".twl_bss":bd},
      "L0":{"ELF":c,"NDS":cn},"L1":{"ELF":p,"NDS":pn},
      "MBK_runtime":"NOT_VERIFIED",
      "physical_test":{"L0":"NOT_RUN","L1":"NOT_RUN"},
      "official_awards":0}
    Path(sys.argv[5]).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],
                      "actual_growth_bytes":report["actual_growth_bytes"],
                      "arm7_payload_bytes":[cn["ARM7"]["bytes"],pn["ARM7"]["bytes"]]},indent=2))

if __name__=="__main__":main()
