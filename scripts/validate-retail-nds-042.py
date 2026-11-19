#!/usr/bin/env python3
"""Validate vanilla nds-bootstrap output structure, not a DSi RA Bridge ROM title.

Build evidence only. This never launches, modifies or installs the NDS.
"""
import argparse,json,struct
from pathlib import Path
def crc16(data):
    c=0xFFFF
    for b in data:
        c^=b
        for _ in range(8):c=(c>>1)^(0xA001 if c&1 else 0)
    return c
def validate(raw):
    if len(raw)<0x200:raise ValueError("ROM truncated")
    title=raw[:12].rstrip(b"\0").decode("ascii","replace")
    game=raw[12:16].decode("ascii","replace")
    if not title or not all(32<=ord(ch)<127 for ch in title) or len(game)!=4 or not all(ch.isalnum() for ch in game):
        raise ValueError("NDS title or game code not printable: "+repr((title,game)))
    if struct.unpack_from("<H",raw,0x15e)[0]!=crc16(raw[:0x15e]):
        raise ValueError("CRC16 invalid")
    if raw[0x12] not in (0,2,3):raise ValueError("invalid NDS unit")
    sections=[]
    for name,offset in (("ARM9",0x20),("ARM7",0x30)):
        rom,entry,ram,size=struct.unpack_from("<4I",raw,offset)
        if not rom>=0x200 or size==0 or rom>=len(raw) or size>len(raw)-rom:
            raise ValueError(name+" segment out of file")
        if not ram<=(entry&~1)<ram+size:
            raise ValueError(name+" invalid entry")
        sections.append({"cpu":name,"rom_offset":rom,"rom_size":size,"ram_start":ram})
    return {"status":"NDS_HEADER_SEGMENTS_VALIDATED_NOT_BOOTED",
            "title":title,"game_code":game,"unit_code":raw[0x12],
            "file_bytes":len(raw),"segments":sections,
            "physical_dsi":"NOT_RUN","retail_game":"NOT_RUN",
            "safe_to_install":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("nds",type=Path)
    p.add_argument("report",type=Path)
    a=p.parse_args()
    result=validate(a.nds.read_bytes())
    with a.report.open("x") as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
