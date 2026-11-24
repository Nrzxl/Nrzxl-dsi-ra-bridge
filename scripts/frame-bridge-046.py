#!/usr/bin/env python3
"""DSi RA Bridge 0.4.6: host-only, versioned synthetic per-frame RAM transport.

OFFLINE laboratory protocol. This is NOT installed in a DSi and does not
authenticate, fetch achievements, submit awards, or network in any way.

A CRC32 detects accidental corruption, NOT an active attacker. An actual
network bridge needs authentication, replay prevention and RA approval.
"""
import argparse
import csv
import io
import json
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

MAGIC = b"DR46"
VERSION = 1
GAME_ID = 9983
GAME_HASH_HEX = "ba3c4052e00c5cc31df5d5534c39de1b"
GAME_HASH = bytes.fromhex(GAME_HASH_HEX)
MAIN = 0
DTCM = 1
BANK_LIMITS = {MAIN: 0x400000, DTCM: 0x4000}
DTCM_BASE = 0x1000000
MAX_REGIONS = 32
MAX_BODY = 1024  # bounded lab packet (~1080 total bytes)
BASE = struct.Struct("<4sBBH16s16sIIHH")
CRC = struct.Struct("<I")
REGION = struct.Struct("<BIH")
STREAM_LENGTH = struct.Struct("<H")


class FrameError(ValueError):
    pass


@dataclass(frozen=True)
class Region:
    bank: int
    offset: int
    data: bytes


@dataclass(frozen=True)
class Frame:
    session: bytes
    game_hash: bytes
    sequence: int
    frame: int
    regions: tuple


def validate_regions(regions):
    if not 1 <= len(regions) <= MAX_REGIONS:
        raise FrameError("Region count out of bounds")
    last_key = None
    for region in regions:
        if region.bank not in BANK_LIMITS or isinstance(region.offset, bool):
            raise FrameError("Unsupported memory bank")
        if not isinstance(region.offset, int) or not isinstance(region.data, bytes):
            raise FrameError("Region fields invalid")
        n = len(region.data)
        if not 1 <= n <= 256:
            raise FrameError("Empty or oversize region")
        if region.offset < 0 or region.offset + n > BANK_LIMITS[region.bank]:
            raise FrameError("Memory range outside mapped bank")
        key = (region.bank, region.offset)
        if last_key is not None:
            if key <= last_key or (region.bank == last_key[0] and
                                   region.offset < last_key[1] + last_key[2]):
                raise FrameError("Regions must be sorted and non-overlapping")
        last_key = (region.bank, region.offset, n)


def encode(frame):
    if (not isinstance(frame.session, bytes) or len(frame.session) != 16 or
            frame.session == bytes(16)):
        raise FrameError("Session must be a nonzero 16-byte identifier")
    if frame.game_hash != GAME_HASH:
        raise FrameError("Game hash mismatch: EU ASMP only")
    if (not isinstance(frame.sequence, int) or not isinstance(frame.frame, int)
            or isinstance(frame.sequence, bool) or isinstance(frame.frame, bool)
            or not 0 <= frame.sequence <= 0xffffffff
            or not 0 <= frame.frame <= 0xffffffff):
        raise FrameError("Sequence/frame out of range")
    validate_regions(frame.regions)
    payload = b"".join(
        REGION.pack(r.bank, r.offset, len(r.data)) + r.data
        for r in frame.regions
    )
    if len(payload) > MAX_BODY:
        raise FrameError("Payload exceeds bounded budget")
    head = BASE.pack(
        MAGIC, VERSION, 0, 0, frame.session, frame.game_hash,
        frame.sequence, frame.frame, len(frame.regions), len(payload)
    )
    check = zlib.crc32(head + payload) & 0xffffffff
    return head + CRC.pack(check) + payload


def decode(packet):
    if len(packet) < BASE.size + CRC.size or len(packet) > BASE.size + CRC.size + MAX_BODY:
        raise FrameError("Packet length invalid")
    magic, version, flags, reserved, session, game_hash, sequence, frame, count, size = BASE.unpack_from(packet)
    if magic != MAGIC or version != VERSION or flags or reserved:
        raise FrameError("Packet version/flags invalid")
    if game_hash != GAME_HASH or session == bytes(16):
        raise FrameError("Session/hash mismatch")
    if not 1 <= count <= MAX_REGIONS or size > MAX_BODY or len(packet) != BASE.size + CRC.size + size:
        raise FrameError("Payload size/count mismatch")
    claimed_crc = CRC.unpack_from(packet, BASE.size)[0]
    payload = packet[BASE.size + CRC.size:]
    actual_crc = zlib.crc32(packet[:BASE.size] + payload) & 0xffffffff
    if actual_crc != claimed_crc:
        raise FrameError("CRC32 mismatch")
    regions = []
    pos = 0
    for _ in range(count):
        if pos + REGION.size > len(payload):
            raise FrameError("Truncated region header")
        bank, offset, length = REGION.unpack_from(payload, pos)
        pos += REGION.size
        if length == 0 or pos + length > len(payload):
            raise FrameError("Truncated/empty region")
        regions.append(Region(bank, offset, payload[pos:pos + length]))
        pos += length
    if pos != len(payload):
        raise FrameError("Trailing data in region payload")
    validate_regions(tuple(regions))
    return Frame(session, game_hash, sequence, frame, tuple(regions))


class Receiver:
    """Strict contiguous frames. Any gap/parse failure locks until new run."""
    def __init__(self):
        self.session = None
        self.next_sequence = 0
        self.next_frame = None
        self.halted = False
        self.accepted = 0
        self.bytes_seen = 0
        self.last = None

    def receive(self, packet):
        if self.halted:
            raise FrameError("Receiver halted; explicit new session required")
        try:
            item = decode(packet)
            if item.sequence != self.next_sequence:
                raise FrameError("Sequence gap/duplicate/reordering")
            if self.session is None:
                self.session = item.session
            elif self.session != item.session:
                raise FrameError("Unexpected session switch")
            if self.next_frame is not None and item.frame != self.next_frame:
                raise FrameError("Missing/duplicate frame")
            if item.frame == 0xffffffff or item.sequence == 0xffffffff:
                raise FrameError("No implicit counter wrap permitted")
            self.next_sequence += 1
            self.next_frame = item.frame + 1
            self.accepted += 1
            self.bytes_seen += len(packet)
            self.last = item
            return item
        except (ValueError, struct.error) as exc:
            self.halted = True
            raise FrameError(str(exc)) from exc

    def read(self, address, count):
        """Read *only* from latest validated frame, no fallback to stale RAM."""
        if self.halted or self.last is None or not 1 <= count <= 256:
            raise FrameError("No valid current frame or invalid read")
        if 0 <= address < BANK_LIMITS[MAIN] and address + count <= BANK_LIMITS[MAIN]:
            bank, relative = MAIN, address
        elif DTCM_BASE <= address < DTCM_BASE + BANK_LIMITS[DTCM] and address + count <= DTCM_BASE + BANK_LIMITS[DTCM]:
            bank, relative = DTCM, address - DTCM_BASE
        else:
            raise FrameError("Read outside supported logical memory")
        # A read must come from the SAME frame and SAME contiguous region.
        for r in self.last.regions:
            if r.bank == bank and r.offset <= relative and relative + count <= r.offset + len(r.data):
                start = relative - r.offset
                return r.data[start:start + count]
        raise FrameError("Unavailable watched bytes: do not reuse earlier frame")


def synthetic_frames():
    session = bytes.fromhex("0460" * 8)
    for seq, (star, coins) in enumerate(((0, 0), (0, 1), (1, 1), (1, 2), (1, 3))):
        # Synthetics at known offsets; NOT real Mario memory values/addresses.
        yield Frame(session, GAME_HASH, seq, seq,
                    (Region(MAIN, 0x100, bytes((star, coins))),
                     Region(DTCM, 0x20, bytes((seq,)))))


def dump_stream(frames):
    result = bytearray()
    for frame in frames:
        wire = encode(frame)
        result.extend(STREAM_LENGTH.pack(len(wire)))
        result.extend(wire)
    return bytes(result)


def load_stream(raw):
    receiver = Receiver()
    pos = 0
    frames = []
    while pos < len(raw):
        if pos + STREAM_LENGTH.size > len(raw):
            receiver.halted = True
            raise FrameError("Truncated packet length")
        size = STREAM_LENGTH.unpack_from(raw, pos)[0]
        pos += STREAM_LENGTH.size
        if size == 0 or size > BASE.size + CRC.size + MAX_BODY or pos + size > len(raw):
            receiver.halted = True
            raise FrameError("Bad framed packet size")
        frames.append(receiver.receive(raw[pos:pos + size]))
        pos += size
    if not frames:
        raise FrameError("Empty stream")
    return frames, receiver


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Generate synthetic-only frame wire + CSV + report")
    demo.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify", help="Verify a frame stream with strict sequence/CRC")
    verify.add_argument("--input", type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.command == "demo":
            args.out.mkdir(parents=True, exist_ok=False)
            stream = dump_stream(list(synthetic_frames()))
            (args.out / "synthetic-frames-046.bin").write_bytes(stream)
            frames, receiver = load_stream(stream)
            rows = []
            for f in frames:
                snapshot = Receiver()
                # Frame-local watcher values, intentionally NOT a network callback.
                stars = next(r.data[0] for r in f.regions if r.bank == MAIN and r.offset == 0x100)
                coins = next(r.data[1] for r in f.regions if r.bank == MAIN and r.offset == 0x100)
                rows.append((f.frame, stars, coins))
            with (args.out / "synthetic-trace-046.csv").open("w", newline="", encoding="ascii") as fp:
                writer = csv.writer(fp, lineterminator="\n")
                writer.writerow(("frame", "stars_synthetic", "coins_synthetic"))
                writer.writerows(rows)
            report = {
                "format": "DSIRB046_HOST_SYNTHETIC_V1",
                "status": "FRAME_TRANSPORT_SYNTHETIC_PASS",
                "game_id": GAME_ID,
                "game_hash": GAME_HASH_HEX,
                "accepted_frames": receiver.accepted,
                "wire_bytes": receiver.bytes_seen,
                "frame_period_ms_target": 1000 / 60,
                "capture_on_dsi": False,
                "verified_against_real_game_ram": False,
                "official_achievement_definitions_used": False,
                "official_unlocks_sent": False,
                "note": "All star/coin values, addresses and achievements are synthetic"
            }
            (args.out / "synthetic-report-046.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(report))
        else:
            inp = args.input
            if not inp.is_file() or inp.stat().st_size > 20_000_000:
                raise FrameError("Missing/oversize stream (>20MB)")
            frames, rec = load_stream(inp.read_bytes())
            print(json.dumps({
                "status": "FRAME_STREAM_VALID_BUT_NOT_PHYSICALLY_AUTHENTICATED",
                "frames": len(frames), "wire_bytes": rec.bytes_seen,
                "last_frame": frames[-1].frame, "official_unlocks_sent": False
            }))
    except (OSError, FrameError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
