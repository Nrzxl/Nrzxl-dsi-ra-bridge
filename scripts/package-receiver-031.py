import argparse
import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--engine", type=Path, required=True)
p.add_argument("--output", type=Path, default=Path("out/receiver-031"))
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
root = a.output / "DSi_RA_Bridge_Receiver_031"
for part in ("protocol", "windows/receiver"):
    shutil.copytree(part, root / part)
shutil.copyfile("Start-Receiver-LAN.cmd", root / "Start-Receiver-LAN.cmd")
(root / "scripts").mkdir()
shutil.copyfile("scripts/audit-capture.cjs", root / "scripts/audit-capture.cjs")
(root / "manifest.json").write_text(json.dumps(dict(version="0.3.1", source_commit=os.environ.get("GITHUB_SHA"), physical_dsi="NOT_RUN", official_submissions=0), indent=2), encoding="utf-8")
(root / "bin").mkdir()
shutil.copyfile(a.engine, root / "bin/dsirb_live.exe")
(root / "docs").mkdir()
shutil.copyfile("docs/network-031.md", root / "docs/network-031.md")
shutil.copyfile("docs/licenses/rcheevos-MIT.txt", root / "bin/rcheevos-MIT.txt")
shutil.copyfile("LICENSE", root / "LICENSE")
files = sorted(x for x in root.rglob("*") if x.is_file())
(root / "SHA256SUMS.txt").write_text("".join(hashlib.sha256(x.read_bytes()).hexdigest()+"  "+x.relative_to(root).as_posix()+"\n" for x in files))
archive = a.output / "DSi_RA_Bridge_Receiver_031.zip"
with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as z:
    for x in sorted(x for x in root.rglob("*") if x.is_file()):
        z.write(x, x.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as check:
    if check.testzip() is not None: raise ValueError("ZIP CRC failure")
print(json.dumps(dict(zip=str(archive), sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
