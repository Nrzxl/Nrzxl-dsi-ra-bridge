#!/usr/bin/env python3
"""047 synthetic 16B watched-memory frames; addresses are NOT Mario addresses.

The pinned rcheevos C runtime may read a wider word than an 8-bit
predicate declares. The 046 demonstration sampled 2 bytes only.
This fixture deliberately provides a bounded 16-byte contiguous watch span,
still offline with synthetic data and NO connection to DSi/RA.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("framebridge046", HERE / "frame-bridge-046.py")
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


def frames():
    for old in b.synthetic_frames():
        small = old.regions[0].data
        main = b.Region(b.MAIN, 0x100, small + bytes(14))
        yield b.Frame(old.session, old.game_hash, old.sequence, old.frame,
                      (main, old.regions[1]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("BLOCKED: target file already exists")
    raw = b.dump_stream(list(frames()))
    _, receiver = b.load_stream(raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(raw)
    print(json.dumps({
        "status": "DSI047_SYNTHETIC_16_BYTE_WATCHED_FIXTURE_PASS",
        "frames": receiver.accepted,
        "captured_from_dsi": False, "official_awards_sent": False
    }))


if __name__ == "__main__":
    main()
