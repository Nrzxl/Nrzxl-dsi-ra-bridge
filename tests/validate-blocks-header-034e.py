#!/usr/bin/env python3
"""Structural NDS/DSi startup probe preflight (accept modern BlocksDS banners).

Unlike the 033 fixture-only validator, newer BlocksDS exports can use a
DSi banner version the 033 check intentionally rejects. Do NOT mistake the
older diagnostic's banner limitation for a malformed binary.
"""
import json
import struct
import sys
from pathlib import Path

def crc16(data):
    c = 0xFFFF
    for b in data:
        c ^= b
        for _ in range(8):
            c = (c >> 1) ^ (0xA001 if c & 1 else 0)
    return c

def check(path):
    size = path.stat().st_size
    with path.open("rb") as file:
        h = file.read(0x4000)
    if size < 0x200 or len(h) < 0x200:
        raise ValueError("truncated NDS")
    actual = struct.unpack_from("<H", h, 0x15E)[0]
    if crc16(h[:0x15E]) != actual:
        raise ValueError("invalid header CRC16")
    region = []
    for label, offset in (("ARM9", 0x20), ("ARM7", 0x30)):
        start, pc, ram, n = struct.unpack_from("<4I", h, offset)
        if n <= 0 or start <= 0 or start > size or n > size - start:
            raise ValueError(label + " invalid file bounds")
        if not (ram <= (pc & ~1) < ram + n):
            raise ValueError(label + " entry outside image")
        region.append(dict(cpu=label, size=n, offset=start))
    banner_offset = struct.unpack_from("<I", h, 0x68)[0]
    banner_version = None
    if banner_offset and banner_offset + 2 <= size:
        with path.open("rb") as file:
            file.seek(banner_offset)
            data = file.read(2)
        if len(data) == 2:
            banner_version = struct.unpack("<H", data)[0]
    return {"status":"STRUCTURAL_NDS_HEADER_PASS_NOT_HARDWARE_TESTED",
            "file_bytes": size, "header_crc16":actual, "sections": region,
            "banner_version":banner_version,
            "banner_version_is_diagnostic_only": True,
            "dsi_boot_proven":False,"official_awards":0}

def main():
    if len(sys.argv) != 2:
        print("usage: python tests/validate-blocks-header-034e.py FILE.nds", file=sys.stderr)
        return 2
    try:
        print(json.dumps(check(Path(sys.argv[1])), indent=2))
    except (ValueError, OSError, struct.error) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
