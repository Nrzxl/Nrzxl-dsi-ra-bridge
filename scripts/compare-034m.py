#!/usr/bin/env python3
"""Offline 034M 1.24 vs 1.25 official BlocksDS ARM7 ELF/NDS reports."""
import json, sys
from pathlib import Path
if len(sys.argv)!=6:
    raise SystemExit("usage: compare-034m.py K0.json K1.json M0.json M1.json report.json")
labels=("K0 SDK124 minimal, physical PASS", "K1 SDK124 DSWiFi, physical WHITE",
        "M0 SDK125 minimal, not run", "M1 SDK125 DSWiFi, not run")
data=[json.loads(Path(p).read_text()) for p in sys.argv[1:5]]
out=[]
for label,d in zip(labels,data):
    s=d.get("elf_program_load_segments",[])
    if len(s)<3 or d["nds_arm7"]["bytes"]<=0:
        raise SystemExit("BLOCKED: invalid ELF/NDS report "+label)
    out.append({
      "label":label,"ARM7_NDS_bytes":d["nds_arm7"]["bytes"],
      "ARM7_entry":d["nds_arm7"]["entry"],
      "ARM7_load_start":d["nds_arm7"]["ram_load_start"],
      "ARM7_load_end":d["nds_arm7"]["ram_load_end"],
      "ELF_LOAD_segments":s,
    })
report={"status":"STATIC_034M_AB_COMPARE_PASS_NOT_HARDWARE_TEST",
        "SDK124_observed":{"K0":"PASS","K1":"WHITE"},
        "SDK125_physical":{"M0":"NOT_RUN","M1":"NOT_RUN"},
        "root_cause":"NOT_ESTABLISHED",
        "run_without_WiFi_calls":True,
        "versions":{"old":"1.24.0","new":"1.25.0"},
        "probes":out,"official_awards":0}
Path(sys.argv[5]).write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],
                  "ARM7_NDS_bytes":{x["label"]:x["ARM7_NDS_bytes"] for x in out}},indent=2))
