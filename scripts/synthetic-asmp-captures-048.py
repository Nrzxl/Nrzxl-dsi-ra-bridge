#!/usr/bin/env python3
"""Synthetic offline 4MiB capture generator for testing 048 without a ROM."""
import argparse
import json
from pathlib import Path

SIZE = 4 * 1024 * 1024
EU_LIVES = 0x09F2F4
SYN_COIN = 0x022220  # invented for QA, NOT a Mario address
SYN_STAR = 0x033330  # invented for QA, NOT a Mario address
SYN_TIMER = 0x044440
STEM = "DSi048_SYNTHETIC_GAME_UNVERIFIED"


def generate(directory):
    directory.mkdir(parents=True, exist_ok=False)
    before = bytearray(SIZE)
    before[EU_LIVES] = 5
    before[SYN_COIN] = 7
    before[SYN_STAR] = 12
    before[SYN_TIMER] = 17
    idle = before.copy()
    idle[SYN_TIMER] = 18
    after = idle.copy()
    after[SYN_COIN] = 8
    after[SYN_TIMER] = 19
    for name, frame, data in (("before", 100, before), ("idle", 120, idle), ("after", 145, after)):
        path = directory / (STEM + "_" + name + ".bin")
        path.write_bytes(data)
        path.with_suffix(".json").write_text(json.dumps({
            "format": "DSIRB048_BIZHAWK_RAM_V1",
            "game_code": "UNVERIFIED",
            "rom_check": "UNVERIFIED",
            "ram_domain": "Main RAM",
            "label": name,
            "frame_before": frame,
            "frame_after": frame,
            "bytes": SIZE,
            "real_emulator_capture": False,
            "dsi_physical": False,
            "official_awards_sent": False
        }, indent=2), encoding="utf-8")
    return directory


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    try:
        generate(args.out)
        print(json.dumps({
            "status": "DSI048_SYNTHETIC_MEMORY_FIXTURES_CREATED",
            "paths": [str(args.out / (STEM + "_" + x + ".bin")) for x in ("before", "idle", "after")],
            "real_game": False,
            "official_awards_sent": False,
        }))
    except (OSError, ValueError) as exc:
        ap.exit(1, "BLOCKED: %s\n" % exc)


if __name__ == "__main__":
    main()
