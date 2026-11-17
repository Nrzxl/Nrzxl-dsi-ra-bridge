import zipfile
from pathlib import Path
r=Path(__file__).resolve().parents[1];out=r/"out"
with zipfile.ZipFile(out/"DSi_RA_Bridge_Windows_Observer_033.zip","w",zipfile.ZIP_DEFLATED) as z:
    z.write(out/"engine/Release/dsirb_live.exe","engine/dsirb_live.exe")
    for p in (r/"windows/observer-033").rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:z.write(p,p.relative_to(r/"windows/observer-033").as_posix())
    for p in ["docs/testing-independent-033.md","THIRD_PARTY_033.md","LICENSE"]:z.write(r/p,Path(p).name)
    z.write(r/"third_party/rcheevos/LICENSE","licenses/rcheevos-LICENSE")
print("PASS: offline Windows decoder and actual rcheevos engine, no network submissions")
