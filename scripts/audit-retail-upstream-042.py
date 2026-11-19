#!/usr/bin/env python3
"""MIT. Audit pinned GPL DScheevos / nds-bootstrap retail hook contracts, read-only.

Never produces installable DS binaries or modifies the upstream checkouts.
"""
import argparse
import json
import subprocess
from pathlib import Path

DSC="59e9978be7b9c3788357ef0a609caf9dc8ea74f3"
BOOT="af351f096dd71a37e0e5b18d9709bcc0fb70342f"
RC="754965ef28db22b0411bfccbde39154cd09e6b79"
def sha(repo):
    return subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()

def must(file, needles):
    source=file.read_text()
    absent=[n for n in needles if n not in source]
    if absent:raise ValueError("%s missing %s"%(file,",".join(absent)))
    return source

def audit(root):
    root=Path(root)
    boot=root/"external/nds-bootstrap"
    rc=root/"external/rcheevos"
    if sha(root)!=DSC or sha(boot)!=BOOT or sha(rc)!=RC:
        raise ValueError("upstream Git SHA mismatch - refuse unreviewed changes")
    hooks=must(boot/"retail/bootloaderi/source/arm7/dscheevos_hooks.c",
      ("patchOsHalt","0xE3A00000","0xEE070F90","0xE12FFF1E",
       'disable("no OS_Halt")','DSCHEEVOS_LOCATION',"fillPmk",
       "readFirmware","wipeSession","dscheevosSetup"))
    asm=must(root/"dscheevos/module/src/start.s",
      ("dscm_vblank_count","vblank_entry:","halt_entry:",
       "mrc","DSCM_VERSION"))
    module=must(root/"dscheevos/module/src/module.c",
      ("vblank_poll","module_idle","rc_client_do_frame"))
    linker=must(root/"dscheevos/module/module.ld",
      ("ORIGIN = 0x02D80000","0x00200000","__stack_top",
       "ASSERT","__image_size"))
    must(root/"README.md",("Work in progress","not approved by RetroAchievements",
                            "not yet tried on a real DSi"))
    if "session" not in hooks or "rc_client_do_frame" not in module:
        raise ValueError("no game runtime evaluation path")
    return {
      "status":"PINNED_SOURCE_HOOK_CONTRACT_PASS_NOT_HARDWARE",
      "upstream_dscheevos_sha":DSC,"upstream_nds_bootstrap_sha":BOOT,
      "upstream_rcheevos_sha":RC,
      "license":"GPL-3.0 upstream module and nds-bootstrap, MIT rcheevos",
      "architecture":{
        "runtime_injection":"ARM7 bootloader patches NitroSDK OS_Halt",
        "per_frame":"ARM7 VBlank count, ARM9 idle evaluation",
        "memory_reserved":"0x02D80000..0x02F80000 (DSi extra RAM / ROM cache)",
        "arm7_replaced_by_041":False},
      "confirmed_hazards":[
        "Upstream launcher requires an online RA session for standard mode",
        "Upstream loader reads Wi-Fi firmware PMK (readFirmware) for reconnect",
        "Upstream wipes its session file after importing",
        "Upstream DS retail bootstrap is not the 041 self-contained launcher",
        "DSi physical test with Flipnote Lenny unproven",
        "Retail ROM overlays/MPU/save/Wi-Fi coexistence still untested here"],
      "hardware_boot_allowed":False,
      "installable_nds_included":False,
      "rom_or_firmware_bytes_read":False,
      "official_achievements_enabled":False,
      "decision":"GATED: do NOT copy the upstream _nds or launch it on DSi yet"
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_root",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    try:
        result=audit(a.source_root)
        s=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output:
            with a.output.open("x",encoding="utf-8") as f:f.write(s)
        print(s,end="")
    except (OSError,subprocess.CalledProcessError,ValueError) as e:
        print(json.dumps({"status":"BLOCKED","reason":str(e)},ensure_ascii=False))
        return 1
    return 0
if __name__=="__main__":raise SystemExit(main())
