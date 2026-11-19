#!/usr/bin/env python3
"""Compare static ELF load segments and section footprint, no physical inference."""
import json
import sys
from pathlib import Path

if len(sys.argv) != 6:
    raise SystemExit("usage: compare-034k-cores.py K0.json K1.json J0.json J1.json out.json")
labels=("K0 minimal","K1 DSWiFi only","J0 Maxmod","J1 DSWiFi Maxmod")
items=[]
for label,filename in zip(labels,sys.argv[1:5]):
    data=json.loads(Path(filename).read_text())
    seg=data["elf_program_load_segments"]
    if not seg or data["nds_arm7"]["bytes"] <= 0:
        raise SystemExit("BLOCKED: malformed ELF report")
    items.append({
        "label":label,
        "arm7_nds_bytes":data["nds_arm7"]["bytes"],
        "nds_load_start":data["nds_arm7"]["ram_load_start"],
        "nds_load_end":data["nds_arm7"]["ram_load_end"],
        "elf_segment_allocations":seg,
        "hardware_boot":"NOT_ESTABLISHED_BY_THIS_REPORT",
    })
report={
    "status":"OFFLINE_STATIC_MEMORY_COMPARISON_PASS_NOT_HARDWARE_PROOF",
    "controls_observed_physically_elsewhere":{"J0":"PASS","J1":"WHITE"},
    "new_physical_tests":{"K0":"NOT_RUN","K1":"NOT_RUN"},
    "bytes":{x["label"]:x["arm7_nds_bytes"] for x in items},
    "probes":items,
    "root_cause":"UNKNOWN",
    "official_awards":0,
}
Path(sys.argv[5]).write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],"bytes":report["bytes"]},indent=2))
