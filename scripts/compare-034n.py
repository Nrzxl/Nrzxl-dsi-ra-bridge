#!/usr/bin/env python3
"""Read-only ELF/NDS comparison for 034N. Firmware state NOT observed."""
import json,sys
from pathlib import Path
if len(sys.argv)!=4:
    raise SystemExit("usage: compare-034n.py N0.json N1.json out.json")
data=[json.loads(Path(x).read_text()) for x in sys.argv[1:3]]
for d in data:
    if not d["elf_program_load_segments"] or not d["nds_arm7"]["bytes"]:
        raise SystemExit("BLOCKED invalid ELF reports")
out={
    "status":"STATIC_AB_VALIDATED_NOT_HARDWARE_PROOF",
    "physical":{"N0_CORE":"NOT_RUN","N1_UPDATE_LINK":"NOT_RUN"},
    "user_actions":"Start N0; only if N0 PASS, try N1 once; white => POWER off",
    "wifi_connectivity":"NOT_INITIALIZED",
    "official_awards":0,
    "root_cause":"NOT_ESTABLISHED",
    "N0_CORE":data[0],
    "N1_UPDATE_LINK":data[1],
    "arm7_nds_bytes_delta":data[1]["nds_arm7"]["bytes"]-data[0]["nds_arm7"]["bytes"]
}
Path(sys.argv[3]).write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({"status":out["status"],
    "N0_bytes":data[0]["nds_arm7"]["bytes"],
    "N1_bytes":data[1]["nds_arm7"]["bytes"],
    "delta_bytes":out["arm7_nds_bytes_delta"]},indent=2))
