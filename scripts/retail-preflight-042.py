#!/usr/bin/env python3
"""MIT. Read-only, offline Nintendo DS ROM preflight. No patches, keys, saves or uploads.

This is NOT an nds-bootstrap compatibility test or active memory observer.
Only game header ranges and optional safe RA logical watch addresses are checked.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

MODULE_START = 0x02D80000
MODULE_END = 0x02F80000
DS_MAIN_END = 0x02400000
WATCH_MAX = 32
MAX_ROM_BYTES = 1024 * 1024 * 1024

def crc16(data):
    c = 0xFFFF
    for v in data:
        c ^= v
        for _ in range(8):
            c = (c >> 1) ^ (0xA001 if c & 1 else 0)
    return c

def rect(a, n, b, m):
    return bool(n and m) and a < b + m and b < a + n

def segment(header, offset, name, rom_bytes, required):
    rom, entry, ram, size = struct.unpack_from("<4I", header, offset)
    if not size:
        if required: raise ValueError("missing " + name)
        return None
    if rom < 0x200 or rom >= rom_bytes or size > rom_bytes - rom:
        raise ValueError(name + " ROM region outside file")
    if ram > 0xFFFFFFFF - size:
        raise ValueError(name + " RAM region overflow")
    if not ram <= (entry & ~1) < ram + size:
        raise ValueError(name + " ARM entry outside mapped code")
    return {"cpu":name,"rom_offset":rom,"rom_size":size,
            "ram_address":ram,"ram_end_exclusive":ram+size,
            "entry":entry,"overlaps_reserved_module":
              rect(ram,size,MODULE_START,MODULE_END-MODULE_START)}

def watchplan(raw):
    if not isinstance(raw,dict) or raw.get("version")!=1:
        raise ValueError("watchplan must be object {version:1, watches:[...]}")
    rows=raw.get("watches")
    if not isinstance(rows,list) or not 1<=len(rows)<=WATCH_MAX:
        raise ValueError("watchplan must contain 1..32 bounded entries")
    watches=[]
    unique=set()
    for i,w in enumerate(rows):
        if not isinstance(w,dict) or set(w)!= {"address","width"}:
            raise ValueError("watch %d requires only address and width"%i)
        addr=w["address"]
        if isinstance(addr,str) and re.fullmatch(r"0x[0-9a-fA-F]{1,8}",addr):
            addr=int(addr,16)
        width=w["width"]
        if type(addr) is not int or type(width) is not int or width not in (1,2,4):
            raise ValueError("invalid watch %d"%i)
        if addr<0 or addr>0xFFFFFFFF or (addr,width) in unique:
            raise ValueError("invalid or duplicated watch %d"%i)
        unique.add((addr,width))
        in_main=addr < 0x400000 and width<=0x400000-addr
        in_dtcm=0x01000000<=addr<0x01004000 and width<=0x01004000-addr
        if not (in_main or in_dtcm):
            raise ValueError("watch %d outside RA DS RAM or DTCM"%i)
        watches.append({"ra_address":addr,"width":width,
                        "region":"DS_MAIN_RAM" if in_main else "DTCM_LOGICAL"})
    return {"status":"BOUNDED_WATCH_PLAN_VALIDATED_NOT_READ",
            "count":len(watches),"watches":watches,
            "important":"DTCM physical base is dynamic CP15; no live read is performed"}

def read_header(path):
    with path.open("rb") as f:
        b=f.read(0x1000)
    if len(b)<0x200: raise ValueError("NDS header truncated")
    if crc16(b[:0x15E])!=struct.unpack_from("<H",b,0x15E)[0]:
        raise ValueError("invalid NDS header CRC16")
    return b

def analyze(path,include_sha=False,watch=None):
    path=Path(path)
    size=path.stat().st_size
    if not 0x200<=size<=MAX_ROM_BYTES: raise ValueError("unsupported ROM file length")
    h=read_header(path)
    unit=h[0x12]
    if unit not in (0,2,3):raise ValueError("invalid unit code")
    segments=[segment(h,0x20,"ARM9",size,True),segment(h,0x30,"ARM7",size,True)]
    if unit in (2,3):
        if len(h)<0x1E0:raise ValueError("DSi extended header truncated")
        for offset,name in ((0x1C0,"ARM9i"),(0x1D0,"ARM7i")):
            v=segment(h,offset,name,size,False)
            if v:segments.append(v)
    raw_title=h[:12].split(b"\0",1)[0].decode("ascii",errors="replace")
    code=h[0xC:0x10].decode("ascii",errors="replace")
    # Sanitize the visible header label, never echo a local path or credentials.
    title="".join(c if " "<=c<="\x7e" else "?" for c in raw_title).strip()[:12]
    game_code="".join(c if c.isalnum() else "?" for c in code)[:4]
    overlaps=[s["cpu"] for s in segments if s["overlaps_reserved_module"]]
    result={
        "schema":"dsirb-retail-preflight-042-v1",
        "status":"OFFLINE_HEADER_PREFLIGHT_ONLY",
        "read_only":True,"game_bytes":size,"title_from_header":title,
        "game_code_from_header":game_code,"unit_code":unit,
        "mode_hint":{0:"DS_NTR",2:"DSi_ENHANCED",3:"DSi_EXCLUSIVE"}[unit],
        "segments":segments,
        "module_reserved_region":["0x02D80000","0x02F80000"],
        "header_segment_overlap":overlaps,
        "retail_bootstrap_compatible":"NOT_DETERMINED",
        "actual_running_memory_compatible":"NOT_DETERMINED",
        "nds_bootstrap_loader":"REQUIRED_FOR_RETAIL_PROBE",
        "observer_active":False,"hardware_executed":False,
        "official_achievements":False,
        "user_owned_rom_required_for_future_game_test":True,
        "reasons":[
           "Header does not describe runtime BSS, overlays, heap, ARM7 cardengine or ROM cache",
           "DScheevos memory module requires a separate bootstrap variant, not the 041 launcher",
           "No ROM, save or firmware files are ever modified or copied by this tool"
        ] }
    if overlaps:result["gate"]="BLOCKED_HEADER_RAM_OVERLAP"
    elif unit != 0:result["gate"]="BLOCKED_DSI_MODE_GAME_UNSUPPORTED_BY_RETAIL_PATH"
    else:result["gate"]="HEADER_ONLY_PASS_MORE_GATES_REQUIRED"
    if watch is not None:result["watch_plan"]=watchplan(watch)
    if include_sha:
        sha=hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda:f.read(8*1024*1024),b""):sha.update(block)
        result["sha256_original_rom"]=sha.hexdigest()
        result["ra_nintendo_ds_hash"]="NOT_CALCULATED_USE_PINNED_RCHEEVOS"
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom",type=Path,help="Your own NDS file, read only, never uploaded")
    p.add_argument("--watch-plan",type=Path,help="Optional bounded RA logical addresses JSON")
    p.add_argument("--sha256",action="store_true",help="Local SHA256 fingerprint, NOT RA hash")
    p.add_argument("--output",type=Path,help="New JSON file; never overwrites")
    a=p.parse_args()
    try:
        wp=json.loads(a.watch_plan.read_text()) if a.watch_plan else None
        result=analyze(a.rom,a.sha256,wp)
        rendered=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output:
            if a.output.resolve()==a.rom.resolve():raise ValueError("output cannot be ROM path")
            with a.output.open("x",encoding="utf-8") as f:f.write(rendered)
        print(rendered,end="")
        return 0 if result["gate"]=="HEADER_ONLY_PASS_MORE_GATES_REQUIRED" else 2
    except (OSError,ValueError,struct.error,KeyError) as e:
        print(json.dumps({"status":"BLOCKED","reason":str(e)},ensure_ascii=False))
        return 3
if __name__=="__main__":raise SystemExit(main())
