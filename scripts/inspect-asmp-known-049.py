#!/usr/bin/env python3
"""049 PC-only known-address inspector; RAM snapshots stay private."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "asmp-eu-known-addresses-049.json"
OLD = ROOT / "scripts" / "analyze-asmp-ram-048.py"
EVENTS = ("coin_up", "star_up", "life_down", "health_down", "level_change", "idle_no_event")

class KnownError(ValueError):
    pass

def reference():
    d = json.loads(CATALOG.read_text(encoding="utf-8"))
    if d.get("format") != "DSIRB049_ASMP_EU_KNOWN_ADDRESSES_V1":
        raise KnownError("Catalog format wrong")
    if d.get("game_code") != "ASMP" or d.get("ram_size_bytes") != 4194304:
        raise KnownError("Catalog region/RAM wrong")
    if not d.get("safety",{}).get("ra_awards_disabled"):
        raise KnownError("Official RA award gate missing")
    seen=set()
    for e in d["entries"]:
        off=int(e["offset_hex"],16)
        addr=int(e["address_hex"],16)
        width=e["width_bytes"]
        if e["id"] in seen or width not in (1,2,4):
            raise KnownError("Duplicate id or bad width")
        if not (0 <= off and off+width <= 4194304 and addr==0x02000000+off):
            raise KnownError("Address out of Main RAM or physical mismatch")
        if not e["sources"] or any(s not in d["sources"] for s in e["sources"]):
            raise KnownError("Missing address source")
        seen.add(e["id"])
    return d

def old_lib():
    spec=importlib.util.spec_from_file_location("dsirb_048_049",OLD)
    lib=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lib)
    return lib

def inspect(paths,event,allow_unverified=False,rom=None,hud_before=None,hud_after=None):
    catalog=reference()
    if event not in EVENTS:
        raise KnownError("Unsupported event")
    if (hud_before is None)!=(hud_after is None):
        raise KnownError("Need both HUD coin values")
    if hud_before is not None and not (0<=hud_before<=255 and 0<=hud_after<=255):
        raise KnownError("HUD coin byte values invalid")
    old=old_lib()
    paths=tuple(Path(p) for p in paths)
    contents=[]
    meta=[]
    for label,path in zip(("before","idle","after"),paths):
        b,m=old.read_capture(path,label)
        contents.append(b)
        meta.append(m)
    suffixes=("_before.bin","_idle.bin","_after.bin")
    resolved=[str(x.resolve()) for x in paths]
    if not all(n.endswith(s) for n,s in zip(resolved,suffixes)):
        raise KnownError("Invalid names for capture phases")
    bases=[n[:-len(s)] for n,s in zip(resolved,suffixes)]
    if len(set(bases))!=1:
        raise KnownError("Mixed capture session")
    frames=[m["frame_before"] for m in meta]
    if not frames[0]<frames[1]<frames[2]:
        raise KnownError("Frames out of order")
    if len(set(m["game_code"] for m in meta))!=1:
        raise KnownError("Game identity changed")
    header_ok=all(m["game_code"]=="ASMP" and
                  m["rom_check"]=="HEADER_MATCH_ONLY" for m in meta)
    local_rom_ok=old.validate_local_rom(rom)
    if not header_ok and not (allow_unverified or local_rom_ok):
        raise KnownError("ASMP header unverified; explicit opt in required")
    rows=[]
    for e in catalog["entries"]:
        off=int(e["offset_hex"],16)
        width=e["width_bytes"]
        vals=[int.from_bytes(b[off:off+width],"little") for b in contents]
        moving_control=vals[0]!=vals[1]
        changed=vals[1]!=vals[2]
        row={
            "id":e["id"],"label":e["label"],"address_hex":e["address_hex"],
            "width_bytes":width,"width_provisional":e["width_provisional"],
            "evidence":e["evidence"],"before":vals[0],"idle":vals[1],
            "after":vals[2],"delta_event":vals[2]-vals[1],
            "control_changed":moving_control,"event_changed":changed,
            "interpretation":("NOISY_CONTROL" if moving_control else
                "CORRELATED_NOT_CAUSAL" if changed else "UNCHANGED")
        }
        if e["id"]=="yellow_coins" and hud_before is not None:
            row["hud_before"]=hud_before
            row["hud_after"]=hud_after
            row["hud_matches_memory"]=(not moving_control and
                vals[1]==hud_before and vals[2]==hud_after)
        rows.append(row)
    return {
      "format":"DSIRB049_ASMP_EU_KNOWN_READONLY_V1",
      "status":"PC_KNOWN_ADDR_OBSERVATION_NOT_RA_CONDITIONS",
      "game_id":9983,"session_id":Path(bases[0]).name,"event":event,
      "frames":dict(zip(("before","idle","after"),frames)),
      "asmp_header_only":header_ok,
      "owned_local_rom_hash_verified":local_rom_ok,
      "active_emulator_rom_hash_verified":False,
      "dsi_physical_tested":False,"official_ra_conditions_used":False,
      "official_awards_sent":False,"raw_dump_bytes_in_report":0,"rows":rows
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for phase in ("before","idle","after"):
        parser.add_argument("--"+phase,required=True,type=Path)
    parser.add_argument("--event",required=True,choices=EVENTS)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--rom",type=Path,help="Local owned ROM checked only on this PC")
    parser.add_argument("--allow-unverified-header",action="store_true")
    parser.add_argument("--expected-coins-before",type=int)
    parser.add_argument("--expected-coins-after",type=int)
    args=parser.parse_args()
    try:
        if args.out.exists():
            raise KnownError("This session/event output exists; no repeated analysis")
        report=inspect((args.before,args.idle,args.after),args.event,
            args.allow_unverified_header,args.rom,
            args.expected_coins_before,args.expected_coins_after)
        if not args.out.parent.is_dir():
            raise KnownError("Output folder missing")
        with args.out.open("x",encoding="utf-8") as fh:
            json.dump(report,fh,ensure_ascii=False,indent=2)
            fh.write("\n")
        print(json.dumps({"status":report["status"],"report":str(args.out),
            "session_id":report["session_id"],"awards_sent":False}))
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc)}),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":
    main()
