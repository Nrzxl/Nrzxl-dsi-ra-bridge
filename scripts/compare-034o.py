#!/usr/bin/env python3
"""Strict, static CPU payload comparison; never opens console network or writes SD."""
import hashlib,json,struct,sys
from pathlib import Path

def info(file):
    d=Path(file).read_bytes()
    if len(d)<0x200:raise ValueError("NDS truncated")
    out={}
    for cpu,offset in (("ARM9",0x20),("ARM7",0x30)):
        rom,entry,ram,size=struct.unpack_from("<4I",d,offset)
        if size==0 or rom<0x200 or rom+size>len(d) or not ram<=(entry&~1)<ram+size:
            raise ValueError(f"{cpu} segment invalid {file}")
        out[cpu]={
            "bytes":size,"sha256":hashlib.sha256(d[rom:rom+size]).hexdigest(),
            "entry":f"0x{entry:08X}","ram_start":f"0x{ram:08X}",
            "ram_end":f"0x{ram+size:08X}"
        }
    return out

if len(sys.argv)!=6:
    raise SystemExit("usage: compare-034o.py baseline_034L.nds O0.nds O1.nds O2.nds report.json")
l0,o0,o1,o2=(info(p) for p in sys.argv[1:5])
if l0["ARM7"]["sha256"]!=o0["ARM7"]["sha256"]:
    raise SystemExit("BLOCKED: O0 ARM7 is not the binary-identical 034L control")
if o0["ARM9"]["sha256"]!=o1["ARM9"]["sha256"]:
    raise SystemExit("BLOCKED: O0 and O1 ARM9 payloads differ")
if o1["ARM7"]["sha256"]!=o2["ARM7"]["sha256"]:
    raise SystemExit("BLOCKED: O1 and O2 ARM7 payloads differ")
if o0["ARM7"]["sha256"]==o1["ARM7"]["sha256"]:
    raise SystemExit("BLOCKED: O1 ARM7 did not change")
if o1["ARM9"]["sha256"]==o2["ARM9"]["sha256"]:
    raise SystemExit("BLOCKED: O2 RX polling was optimized out")
report={
    "status":"STATIC_AB_SDK124_VALID_NOT_HARDWARE_PROOF",
    "sdk":"BlocksDS v1.24.0 pinned",
    "controls":{"034L_L0":"PHYSICAL_PASS","O0_UI_ONLY":"NOT_RUN",
                "O1_ARM7_SEND_ONLY":"NOT_RUN","O2_ARM9_RX_POLL":"NOT_RUN"},
    "identical_cpu_payloads":{
       "L0_ARM7_equals_O0_ARM7":True,
       "O0_ARM9_equals_O1_ARM9":True,
       "O1_ARM7_equals_O2_ARM7":True
    },
    "root_cause":"UNKNOWN","connection":"NO_NETWORK",
    "official_awards":0,
    "samples":{"L0":l0,"O0":o0,"O1":o1,"O2":o2}
}
Path(sys.argv[5]).write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],
                   "cpu_bytes":{k:{"ARM7":v["ARM7"]["bytes"],"ARM9":v["ARM9"]["bytes"]}
                                for k,v in report["samples"].items()}},indent=2))
