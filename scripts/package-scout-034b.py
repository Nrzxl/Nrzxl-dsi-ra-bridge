#!/usr/bin/env python3
"""Build a removable SD-only homebrew scout ZIP; NEVER packages a retail ROM."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

FILES = ("nds/DSiRABridge_034B/DSIRB_Scout_034B.nds",)
GUIDE = """# DSi RA Bridge 034B - scout experimental

NOT_RUN in physical DSi XL. NOT a retail monitor, not an RA client.
No release, no Unlaunch, no boot.nds/private/TWiLight++ replacement.

1. Power off and back up the SD before testing.
2. Extract on a PC and copy ONLY nds/DSiRABridge_034B/ to the internal SD.
   Do not touch older DSiRABridge_020/030/031/032/033 folders.
3. Enter existing Flipnote Lenny -> HBMenu. Run DSIRB_Scout_034B.nds.
4. Photograph DSi mode, Internal sd, Own hash and VBlank counter.
   The scout uses only a private 4 KiB buffer, does not reserve retail RAM.
5. Wait for 300 frames and press X once if both DSi mode/internal sd say YES.
   This saves only version/mode/frame/owned-buffer metadata into
   sd:/DSiRABridge_034B/SCOUT000.txt (or next unused number).
6. Press START; turn off the console before removing the SD.
7. Share SCOUTnnn.txt and photo privately for validation.
   Do NOT share NAND/OTP/keys/saves/ROMs/console IDs.
8. For removal delete ONLY nds/DSiRABridge_034B and DSiRABridge_034B.

If DSi mode or sd:/ is NO, this gate is BLOCKED: do not adjust firmware,
SCFG/MBK, Unlaunch or boot files to work around it.
This test does not run a game or establish DScheevos compatibility.
"""


def add(z, path, data):
    info = zipfile.ZipInfo(path, (2026, 11, 18, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(info, data)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--commit", required=True)
    args = p.parse_args()
    blob = args.binary.read_bytes()
    if len(blob) < 512 or len(blob) > 4 * 1024 * 1024:
        raise ValueError("scout binary outside expected bounds")
    if not (len(args.commit) == 40 and all(c in "0123456789abcdef" for c in args.commit)):
        raise ValueError("invalid source commit")
    sha = hashlib.sha256(blob).hexdigest()
    status = dict(version="0.3.4-B-scout", commit=args.commit,
                  physical_dsi="NOT_RUN", retail_monitor="NOT_IMPLEMENTED",
                  nds_binary_sha256=sha, official_awards=0,
                  network="NOT_USED", firmware_written=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w") as archive:
        add(archive, FILES[0], blob)
        add(archive, "TESTE_034B.md", GUIDE.encode("utf-8"))
        add(archive, "STATUS.json", (json.dumps(status, indent=2) + "\n").encode())
        add(archive, "SHA256SUMS.txt", (sha + "  " + FILES[0] + "\n").encode())
    print(json.dumps(dict(status="PACKAGED_SOURCE_ONLY_BUILD", nds_sha256=sha,
                          zip=str(args.output), physical="NOT_RUN")))


if __name__ == "__main__":
    main()
