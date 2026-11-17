import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--engine", type=Path, required=True)
p.add_argument("--output", type=Path, default=Path("out/receiver-030"))
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
root = a.output / "DSi_RA_Bridge_Receiver_030"
for part in ("protocol", "windows/receiver"):
    shutil.copytree(part, root / part)
(root / "bin").mkdir()
shutil.copyfile(a.engine, root / "bin/dsirb_live.exe")
(root / "docs").mkdir()
shutil.copyfile("docs/network-030.md", root / "docs/network-030.md")
shutil.copyfile("docs/licenses/rcheevos-MIT.txt", root / "bin/rcheevos-MIT.txt")
shutil.copyfile("LICENSE", root / "LICENSE")
files = sorted(x for x in root.rglob("*") if x.is_file())
(root / "SHA256SUMS.txt").write_text("".join(hashlib.sha256(x.read_bytes()).hexdigest()+"  "+x.relative_to(root).as_posix()+"\n" for x in files))
archive = a.output / "DSi_RA_Bridge_Receiver_030.zip"
with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as z:
    for x in sorted(x for x in root.rglob("*") if x.is_file()):
        z.write(x, x.relative_to(root).as_posix())
print(json.dumps(dict(zip=str(archive), sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
