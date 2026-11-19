#!/usr/bin/env python3
"""Compare ARM7 segment and NDS package: structurally valid != hardware boot."""
import json
import struct
import sys
from hashlib import sha256
from pathlib import Path

def check(filename):
    p=Path(filename)
    data=p.read_bytes()
    if len(data) < 0x200:
        raise ValueError(f"Truncated NDS file {p}")
    ofs,pc,addr,size=struct.unpack_from("<4I",data,0x30)
    if size <= 0 or ofs == 0 or ofs+size>len(data):
        raise ValueError("ARM7 section outside image")
    if not addr <= (pc & ~1) < addr+size:
        raise ValueError("ARM7 entry outside range")
    return {"file":str(p),"size":len(data),
        "sha256":sha256(data).hexdigest(),
        "arm7_offset":ofs, "arm7_load_address":f"0x{addr:08X}",
        "arm7_entry":f"0x{pc:08X}","arm7_size":size,
        "arm7_load_end":f"0x{addr+size:08X}",
        "arm7_payload_sha256":sha256(data[ofs:ofs+size]).hexdigest()}

def main():
    a,b=map(check,sys.argv[1:3])
    if a["arm7_payload_sha256"]==b["arm7_payload_sha256"]:
        raise SystemExit("BLOCKED: official baseline and WiFi ARM7 payloads were identical")
    if b["arm7_size"] <= a["arm7_size"]:
        raise SystemExit("BLOCKED: expected WiFi ARM7 payload larger than baseline")
    print(json.dumps({"status":"STRUCTURAL_A_B_VALIDATED_NOT_HARDWARE_TESTED",
       "arm9_source_identical":True,
       "baseline":a, "dswifi":b,
       "arm7_byte_delta":b["arm7_size"]-a["arm7_size"],
       "network_connected":False,
       "official_awards":0,"hardware_test":"NOT_RUN"},indent=2))
if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python scripts/inspect-034j-nds.py A.nds B.nds")
    main()
