#!/usr/bin/env python3
"""Fail-closed byte comparison of O2 and 034P CPU payloads in NDS headers.

Physical status is always NOT_RUN for new probes. This script is static only.
"""
import hashlib,json,struct,sys
from pathlib import Path

def cpu_segments(filename):
    blob=Path(filename).read_bytes()
    if len(blob)<0x200:
        raise RuntimeError("NDS truncated")
    out={}
    for cpu,offset in (("arm9",0x20),("arm7",0x30)):
        rom,entry,load,size=struct.unpack_from("<4I",blob,offset)
        if size<=0 or rom<0x200 or rom+size>len(blob) or not load<=(entry&~1)<load+size:
            raise RuntimeError(f"BLOCKED invalid {cpu} in {filename}")
        out[cpu]={
            "bytes":size,
            "sha256":hashlib.sha256(blob[rom:rom+size]).hexdigest(),
            "entry":f"0x{entry:08X}",
            "ram_load_start":f"0x{load:08X}",
            "ram_load_end":f"0x{load+size:08X}",
        }
    return out

def main():
    if len(sys.argv)!=6:
        raise SystemExit("usage: compare-034p.py O2.nds P0.nds P1.nds P2.nds report.json")
    o2,p0,p1,p2=map(cpu_segments,sys.argv[1:5])
    if o2["arm9"]["sha256"]!=p0["arm9"]["sha256"]:
        raise SystemExit("BLOCKED P0 ARM9 differs from physical PASS O2")
    if o2["arm7"]["sha256"]!=p0["arm7"]["sha256"]:
        raise SystemExit("BLOCKED P0 ARM7 differs from physical PASS O2")
    if not (p0["arm9"]["sha256"]==p1["arm9"]["sha256"]==p2["arm9"]["sha256"]):
        raise SystemExit("BLOCKED P0/P1/P2 ARM9 payloads differ")
    if p0["arm7"]["sha256"]==p1["arm7"]["sha256"]:
        raise SystemExit("BLOCKED P1 ARM7 did not change")
    if p1["arm7"]["sha256"]==p2["arm7"]["sha256"]:
        raise SystemExit("BLOCKED P2 ARM7 did not change")
    results={"O2_physically_PASS":o2,"P0":p0,"P1":p1,"P2":p2}
    report={
      "status":"STATIC_AB_CPU_BYTES_PASS_PHYSICAL_NOT_RUN",
      "baseline":"034O O2 both stages REACHED confirmed physically via Flipnote Lenny/HBMenu",
      "blocksds":"v1.24.0 pinned",
      "checks":{"O2_ARM9_equals_P0":True,"O2_ARM7_equals_P0":True,
                "P0_P1_P2_ARM9_identical":True,
                "P1_ARM7_differs":True,"P2_ARM7_differs":True},
      "arm7_payload_bytes":{k:v["arm7"]["bytes"] for k,v in results.items()},
      "physical_results":{"P0":"NOT_RUN","P1":"NOT_RUN","P2":"NOT_RUN"},
      "wifi_functions_invoked_by_our_sources":False,
      "wifi_connected":False,"root_cause":"NOT_ESTABLISHED","official_awards":0,
      "binaries":results
    }
    Path(sys.argv[5]).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],
      "arm7_payload_bytes":report["arm7_payload_bytes"]},indent=2))

if __name__=="__main__":main()
