#!/usr/bin/env python3
"""0.3.4-B declared-memory gate. Read-only ROM inspection, NOT runtime proof."""
import argparse
import json
import struct
from pathlib import Path

from retail_preflight_034 import inspect_rom

MODULE_START = 0x02D80000
MODULE_END = 0x02F80000
OVERLAY_LIMIT = 4096
ENTRY_BYTES = 32


def ensure(ok, message):
    if not ok:
        raise ValueError(message)


def u32(data, at):
    return struct.unpack_from("<I", data, at)[0]


def intersects(a, b, c, d):
    return a < d and c < b


def overlay_ranges(stream, file_size, header_size, table_offset, table_size, label):
    if table_offset == 0 and table_size == 0:
        return []
    ensure(table_offset != 0 and table_size != 0, label + ": incomplete table")
    ensure(table_offset % 4 == 0 and table_size % ENTRY_BYTES == 0,
           label + ": invalid alignment/size")
    ensure(table_size // ENTRY_BYTES <= OVERLAY_LIMIT,
           label + ": too many entries")
    ensure(table_offset >= header_size and table_offset <= file_size and
           table_size <= file_size - table_offset, label + ": truncated table")
    stream.seek(table_offset)
    data = stream.read(table_size)
    ensure(len(data) == table_size, label + ": unreadable table")
    rows = []
    for idx in range(table_size // ENTRY_BYTES):
        row = data[idx * ENTRY_BYTES:(idx + 1) * ENTRY_BYTES]
        overlay_id, address, size, bss, static_start, static_end, file_id, flags = (
            struct.unpack("<8I", row)
        )
        ensure(size + bss != 0, label + ": zero-sized overlay")
        ensure(0x02000000 <= address < 0x04000000 and
               size + bss <= 0x04000000 - address,
               label + ": invalid RAM/BSS footprint")
        ensure(static_start <= static_end,
               label + ": reversed static init range")
        rows.append({"section": label, "overlay_id": overlay_id,
                     "ram_start": address, "ram_end": address + size + bss,
                     "ram_bytes": size, "bss_bytes": bss})
    return rows


def inspect(path):
    preflight = inspect_rom(path)
    ensure(preflight["status"] == "STRUCTURE_PASS_RETAIL_MONITOR_NOT_PROVEN",
           "baseline preflight failed")
    file_size = preflight["rom_bytes"]
    with path.open("rb") as stream:
        header = stream.read(0x1000)
        regions = []
        for name, offset, size in (("ARM9", 0x50, 0x54),
                                   ("ARM7", 0x58, 0x5C)):
            regions.extend(overlay_ranges(
                stream, file_size, preflight["header_bytes"],
                u32(header, offset), u32(header, size), name))
    declared = []
    for segment in preflight["segments"]:
        start = int(segment["load_address"], 16)
        end = start + segment["file_bytes"]
        declared.append({"section": segment["name"] + " binary",
                         "ram_start": start, "ram_end": end})
    declared.extend(regions)
    overlaps = [dict(section=x["section"], ram_start=f"0x{x['ram_start']:08X}",
                     ram_end=f"0x{x['ram_end']:08X}")
                for x in declared if intersects(
                    x["ram_start"], x["ram_end"], MODULE_START, MODULE_END)]
    return {
        "version": "0.3.4-B",
        "status": ("BLOCKED_DECLARED_RESERVATION_OVERLAP" if overlaps else
                   "NO_DECLARED_OVERLAP_RUNTIME_UNPROVEN"),
        "unit_code": preflight["unit_code"],
        "rom_bytes": file_size,
        "candidate_module_window": {
            "start": f"0x{MODULE_START:08X}",
            "end_exclusive": f"0x{MODULE_END:08X}",
            "origin": "Pinned DScheevos prototype RAM budget; NOT allocatable without a bootstrap fork",
        },
        "declared_arm_sections": len(preflight["segments"]),
        "declared_overlay_entries": len(regions),
        "declared_overlaps": overlaps,
        "retail_monitor_ready": False,
        "safe_to_patch": False,
        "official_awards": 0,
        "additional_gates": [
            "Retail nds-bootstrap loader may reserve this RAM for its ROM cache",
            "ROM header cannot describe runtime heap, relocated sections or all overlays",
            "DSi mode/SCFG/MBK/SDIO via Flipnote Lenny untested for a retail loader",
            "No resident hook/OS_Halt patch, live DTCM capture, saves or frame evaluation",
            "PEER TIMEOUT 032 remains OPEN; official RA client authorization pending",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_nds", type=Path, help="local owned ROM; never uploaded")
    args = parser.parse_args()
    try:
        result = inspect(args.original_nds)
    except (OSError, ValueError, struct.error) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc),
                          "rom_modified": False, "retail_monitor_ready": False}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 3 if result["declared_overlaps"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
