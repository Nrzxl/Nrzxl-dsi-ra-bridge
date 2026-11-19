#!/usr/bin/env python3
"""Package pinned source-built isolated NTR retail loader, offline-only 034C gate.

Never changes the user's SD, never includes games or credentials.
The package is NOT a Release and has NOT been tested on real hardware.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ZIP_DATE = (2026, 11, 19, 0, 0, 0)
GAME = "DSiRABridge_034C/games/selected.nds"
SAVE = "DSiRABridge_034C/saves/selected.sav"

INI = f"""[NDS-BOOTSTRAP]
NDS_PATH = sd:/{GAME}
SAV_PATH = sd:/{SAVE}
DSI_MODE = 0
BOOST_CPU = 0
BOOST_VRAM = 0
LANGUAGE = -1
LOGGING = 0
DEBUG = 0
SAVE_RELOCATION = 1
GAME_SOFT_RESET = 0
CHEAT_PATH =
"""

SETTINGS = """[DSCHEEVOS]
ENABLED = 0
HARDCORE = 0
SEND_DURING_PLAY = 0
SPECTATOR = 1
USERNAME =
TOKEN =
"""

GUIDE = """# DSi RA Bridge 0.3.4-C: experimental isolated offline NTR boot

DO NOT RUN ON THE PRIMARY SD WITHOUT BACKUP AND A SECOND TEST CARD.
This gate is NOT approved or tested on physical hardware. It does NOT earn
RetroAchievements and MUST NOT be installed over stable TWiLight++.

There are no ROMs or saves in this package. Only run on a test SD after
the GitHub build, source bundle and independent static path review PASS.

Package directories (no overwrites of stable TWiLight++ paths):
  nds/DSiRABridge_034C/DSIRB_Launcher_034C.nds
  _nds/dsirb034c/{nds-bootstrap.nds,dscheevos9.bin,load.bin,nds-bootstrap.ini,dscheevos.ini}
  _nds/dsirb034c-cache/
  DSiRABridge_034C/{games/,saves/}

The two .ini files are hardcoded to launch:
  sd:/DSiRABridge_034C/games/selected.nds
and use the isolated save:
  sd:/DSiRABridge_034C/saves/selected.sav
Do not include a game ROM in any GitHub Issue, Release or artifact.

PHYSICAL EXPERIMENT **BLOCKED until reviewed**:
1. Make an image/backup of the existing SD. Prefer an independent spare SD.
2. Verify the SD doesn't have _nds/dsirb034c or DSiRABridge_034C; never overwrite.
3. Copy only new experimental directories from the ZIP to the spare SD.
4. Copy a legal personal backup of a compatible NTR game to the exact
   selected.nds location; verify hash/structure locally before boot.
5. Launch the experimental .nds from Flipnote Lenny -> HBMenu.
6. Offline run only: DSCHEEVOS ENABLED=0, no credentials, no RA network,
   no award requests; confirm the game boots, saves, sound, controls.
7. If any loader shows an unexpected path or asks for login, STOP immediately.
8. Report results privately, and remove only our directories on test SD.
9. Do not run this on original SD until tests of isolation are complete.

We do not know if this DScheevos fork will boot this game on DSi XL
via Flipnote Lenny, or if it will clash with runtime memory or caches.
The SCOUT034B success is not proof of retail boot compatibility.
"""

def add(archive, name, data):
    if name.startswith("/") or "\\" in name or ".." in Path(name).parts:
        raise ValueError("unsafe package path")
    if name.startswith("_nds/nds-bootstrap") or name.startswith("_nds/dscheevos") or name == "boot.nds":
        raise ValueError("would overwrite stable files")
    entry = zipfile.ZipInfo(name, ZIP_DATE)
    entry.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(entry, data)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--commit", required=True)
    a = p.parse_args()
    if len(a.commit) != 40 or any(c not in "0123456789abcdef" for c in a.commit):
        raise ValueError("bad source commit")
    binary = {
        "nds/DSiRABridge_034C/DSIRB_Launcher_034C.nds":
            "dscheevos/launcher/dscheevos-launcher.nds",
        "_nds/dsirb034c/nds-bootstrap.nds":
            "external/nds-bootstrap/bin/nds-bootstrap-nightly.nds",
        "_nds/dsirb034c/dscheevos9.bin":
            "dscheevos/module/build/dscheevos9.bin",
        "_nds/dsirb034c/load.bin":
            "dscheevos/launcher/loader/out/load.bin",
    }
    licenses = {
        "_nds/dsirb034c/licenses/dscheevos-GPL-3.txt": "LICENSE",
        "_nds/dsirb034c/licenses/nds-bootstrap-GPL-3.txt": "external/nds-bootstrap/LICENSE",
        "_nds/dsirb034c/licenses/rcheevos.txt": "external/rcheevos/LICENSE",
        "_nds/dsirb034c/licenses/mbedtls.txt": "external/mbedtls/LICENSE",
        "_nds/dsirb034c/licenses/lwip.txt": "external/lwip/COPYING",
    }
    files = {}
    for target, src in {**binary, **licenses}.items():
        data = (a.upstream / src).read_bytes()
        if target in binary and not 512 <= len(data) <= 16*1024*1024:
            raise ValueError("invalid binary " + src)
        files[target] = data
    files.update({
        "_nds/dsirb034c/nds-bootstrap.ini": INI.encode(),
        "_nds/dsirb034c/dscheevos.ini": SETTINGS.encode(),
        "nds/DSiRABridge_034C/README.txt": GUIDE.encode(),
        "_nds/dsirb034c/README.txt": GUIDE.encode(),
    })
    status = {
        "version": "0.3.4-C-offline-only",
        "bridge_commit": a.commit,
        "upstream": "skierrz/dscheevos@59e9978be7b9c3788357ef0a609caf9dc8ea74f3",
        "bootstrap": "skierrz/nds-bootstrap@af351f096dd71a37e0e5b18d9709bcc0fb70342f",
        "physical_test": "NOT_RUN",
        "game_boot": "NOT_RUN",
        "retail_monitor": "NOT_ENABLED",
        "retroachievements": "DISABLED",
        "offline_by_default": True, "official_awards": 0,
        "no_game_in_package": True,
        "no_stable_paths_written_by_installer": True,
        "no_release": True,
        "checksums": {name: hashlib.sha256(files[name]).hexdigest() for name in binary},
    }
    files["STATUS.json"] = (json.dumps(status, indent=2) + "\n").encode()
    sha_lines = [
        hashlib.sha256(data).hexdigest() + "  " + name
        for name, data in sorted(files.items())
    ]
    files["SHA256SUMS.txt"] = ("\n".join(sha_lines) + "\n").encode()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.output, "w") as z:
        for name, data in sorted(files.items()):
            add(z, name, data)
    with zipfile.ZipFile(a.output) as z:
        names = set(z.namelist())
        if len(names) != len(files) or not names == set(files):
            raise ValueError("package file mismatch")
        for name in names:
            if name.startswith("_nds/nds-bootstrap") or name.startswith("_nds/dscheevos"):
                raise ValueError("would overwrite stable paths")
    print(json.dumps({"status": "OFFLINE_STAGING_PREPARED_NOT_RUN",
                      "zip": str(a.output), "files": len(files),
                      "physical_dsi": "NOT_RUN", "official_awards": 0}))


if __name__ == "__main__":
    main()
