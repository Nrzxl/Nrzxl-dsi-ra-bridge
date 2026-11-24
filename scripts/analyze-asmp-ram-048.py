#!/usr/bin/env python3
"""DSi RA Bridge 048: local read-only ASMP EU main-RAM differential analyzer.

The three 4 MiB files must come from the user's own BizHawk/melonDS DS game.
No ROM inspection, saves, credential handling, Internet, game writes or awards.
Only sanitized offsets and measurements are emitted. Input dumps are PRIVATE.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

SIZE = 4 * 1024 * 1024
EVENTS = {"coin_up", "star_up", "life_down", "health_down", "level_change"}
EU_REFERENCE = {
    0x09F2F4: ("lives", "Hack64 Skelux Super Mario 64 DS Europe"),
    0x11117C: ("health_candidate_a", "Hack64 Skelux Super Mario 64 DS Europe"),
    0x092144: ("health_candidate_b", "Hack64 Skelux Super Mario 64 DS Europe"),
    0x09F2F8: ("level_id", "Hack64 Skelux Super Mario 64 DS Europe"),
}


class CaptureError(ValueError):
    pass


def read_capture(path, label):
    if not path.is_file() or path.stat().st_size != SIZE:
        raise CaptureError("RAM capture must be exactly 4194304 bytes")
    meta_path = path.with_suffix(".json")
    if not meta_path.is_file() or meta_path.stat().st_size > 16_384:
        raise CaptureError("Missing/oversize capture metadata JSON")
    meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
    if not isinstance(meta, dict):
        raise CaptureError("Invalid capture metadata")
    if meta.get("format") != "DSIRB048_BIZHAWK_RAM_V1" or meta.get("label") != label:
        raise CaptureError("Capture format/label mismatch")
    if meta.get("bytes") != SIZE or meta.get("ram_domain") != "Main RAM":
        raise CaptureError("RAM domain/size mismatch")
    if meta.get("dsi_physical") is not False or meta.get("official_awards_sent") is not False:
        raise CaptureError("Untrusted capture provenance flags")
    before, after = meta.get("frame_before"), meta.get("frame_after")
    if not isinstance(before, int) or isinstance(before, bool) or before < 0 or before != after:
        raise CaptureError("Snapshot not atomic by emulator frame counter")
    if meta.get("game_code") not in ("ASMP", "UNVERIFIED"):
        raise CaptureError("Wrong game header / source")
    if meta.get("rom_check") not in ("HEADER_MATCH_ONLY", "UNVERIFIED"):
        raise CaptureError("ROM check state invalid")
    if (meta["game_code"] == "ASMP") != (meta["rom_check"] == "HEADER_MATCH_ONLY"):
        raise CaptureError("ROM header/check state inconsistent")
    return path.read_bytes(), meta


def compatible_pair(event, old, new, width):
    maximum = (1 << (8 * width)) - 1
    if event in ("coin_up", "star_up"):
        if old > (150 if event == "star_up" else 100):
            return False
        return new == old + 1
    if event == "life_down":
        return old <= 100 and old > 0 and new == old - 1
    if event == "health_down":
        return 0 < old <= maximum and 0 <= new < old
    return old != new


def analyze(before, idle, after, event, limit=80):
    if event not in EVENTS:
        raise CaptureError("Unknown event")
    if not len(before) == len(idle) == len(after) == SIZE:
        raise CaptureError("Input byte size mismatch")
    # A live game often changes timers, coordinates and RNG even at idle.
    # Strictly exclude all byte offsets that varied in the control interval.
    baseline_moving = sum(x != y for x, y in zip(before, idle))
    action_moving = sum(x != y for x, y in zip(idle, after))
    candidates = []
    for offset in range(SIZE):
        if before[offset] != idle[offset] or idle[offset] == after[offset]:
            continue
        for width in (1, 2, 4):
            if offset % width or offset + width > SIZE:
                continue
            a = before[offset:offset + width]
            b = idle[offset:offset + width]
            c = after[offset:offset + width]
            if a != b or b == c:
                continue
            old = int.from_bytes(b, "little")
            new = int.from_bytes(c, "little")
            if not compatible_pair(event, old, new, width):
                continue
            referenced = EU_REFERENCE.get(offset)
            score = (100 if referenced else 0) + (4 if width == 1 else (2 if width == 2 else 1))
            # These are HYPOTHESES; independent repetitions must validate.
            candidates.append({
                "logical_ram_offset_hex": "0x%06X" % offset,
                "physical_arm9_address_hex": "0x%08X" % (0x02000000 + offset),
                "width_bytes": width,
                "before_value": old,
                "after_value": new,
                "delta": new - old,
                "score": score,
                "eu_literature_hint": referenced[0] if referenced else None,
                "confidence": "HYPOTHESIS_NEEDS_REPLICATION",
            })
    candidates.sort(key=lambda c: (-c["score"], int(c["logical_ram_offset_hex"], 16), c["width_bytes"]))
    return {
        "event": event,
        "total_candidates": len(candidates),
        "candidate_rows_in_report": min(limit, len(candidates)),
        "bytes_changed_during_control": baseline_moving,
        "bytes_changed_during_event": action_moving,
        "suggested_candidates": candidates[:limit],
    }


def summary(paths, event, limit, allow_unverified):
    contents = []
    metadata = []
    for name, path in zip(("before", "idle", "after"), paths):
        data, meta = read_capture(path, name)
        contents.append(data)
        metadata.append(meta)
    base = [str(x.with_suffix("")) for x in paths]
    if not (base[0].endswith("_before") and base[1] == base[0][:-7] + "_idle" and
            base[2] == base[0][:-7] + "_after"):
        raise CaptureError("Captures are not from the same labeled session")
    if not (metadata[0]["frame_before"] < metadata[1]["frame_before"] <
            metadata[2]["frame_before"]):
        raise CaptureError("Capture frames not strictly increasing")
    verified = all(x["rom_check"] == "HEADER_MATCH_ONLY" for x in metadata)
    if not verified and not allow_unverified:
        raise CaptureError("ROM game code unverified by emulator; add --allow-unverified-header ONLY after local ASMP hash check")
    if any(x["game_code"] != metadata[0]["game_code"] for x in metadata):
        raise CaptureError("ROM identity changed between snapshots")
    outcome = analyze(*contents, event=event, limit=limit)
    return {
        "format": "DSIRB048_RAM_DIFF_SANITIZED_V1",
        "status": "EMULATOR_RAM_EVENT_CANDIDATES_NOT_RA_VERIFIED",
        "game_id": 9983,
        "expected_game_code": "ASMP",
        "game_header_seen_by_bizhawk": metadata[0]["game_code"],
        "cartridge_header_verification": "ASMP_HEADER_MATCH_ONLY" if verified else "USER_OVERRIDDEN_UNVERIFIED",
        "rom_ra_hash_verified_by_analyzer": False,
        "sampled_ram_bytes": SIZE,
        "first_frame": metadata[0]["frame_before"],
        "control_frame": metadata[1]["frame_before"],
        "event_frame": metadata[2]["frame_before"],
        "dsi_physical_tested": False,
        "official_ra_conditions_used": False,
        "official_unlocks_sent": False,
        "explanation": "Local PC RAM correlations only; not atomic DS hardware frames or confirmed RA addresses",
        **outcome,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "idle", "after"):
        ap.add_argument("--" + name, required=True, type=Path)
    ap.add_argument("--event", required=True, choices=sorted(EVENTS))
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--allow-unverified-header", action="store_true")
    ap.add_argument("--max-results", type=int, default=80)
    args = ap.parse_args()
    try:
        if not 1 <= args.max_results <= 200:
            raise CaptureError("--max-results must be 1..200")
        if args.out.exists():
            raise CaptureError("Refusing to overwrite existing report")
        report = summary(
            (args.before, args.idle, args.after),
            event=args.event, limit=args.max_results,
            allow_unverified=args.allow_unverified_header
        )
        if not args.out.parent.is_dir():
            raise CaptureError("Output directory does not exist")
        with args.out.open("x", encoding="utf-8") as out:
            json.dump(report, out, indent=2)
            out.write("\n")
        print(json.dumps({
            "status": report["status"], "event": report["event"],
            "total_candidates": report["total_candidates"],
            "rom_ra_hash_verified_by_analyzer": False,
            "official_unlocks_sent": False,
            "report": str(args.out)
        }))
    except (OSError, json.JSONDecodeError, CaptureError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
