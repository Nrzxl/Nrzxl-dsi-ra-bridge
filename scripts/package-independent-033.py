import json,zipfile,hashlib,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/"out";build=out/"independent-first"
proof=json.loads((out/"emulation/validation.json").read_text());assert proof["status"]=="PASS"
stage=out/"SD_033_EMULATOR_VALIDATED_PHYSICAL_NOT_RUN";stage.mkdir()
def copy(src,dst):
    p=stage/dst;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(src.read_bytes())
copy(build/"DSiRABridge_Launcher_A_033.nds","nds/DSiRABridge_033/Launcher_A_033.nds")
copy(build/"DSiRABridge_Fixture_B_033.nds","nds/DSiRABridge_033/Fixture_B_033_control.nds")
copy(build/"instrumented/Fixture_B_033_observed.nds","DSiRABridge_033/Fixture_B_033_observed.nds")
copy(build/"instrumented/instrumentation.json","DSiRABridge_033/instrumentation.json")
copy(root/"docs/testing-independent-033.md","TESTE_033.md")
copy(root/"dsi/launcher-033-gpl/COPYING","licenses/launcher-GPL-2.txt")
copy(root/"THIRD_PARTY_033.md","licenses/THIRD_PARTY_033.md")
for f in (build/"licenses").rglob("*"):
    if f.is_file():copy(f,"licenses/SDK/"+f.relative_to(build/"licenses").as_posix())
(stage/"STATUS.json").write_text(json.dumps(dict(version="0.3.3-experimental",commit=os.environ.get("GITHUB_SHA"),full_nds_emulation="PASS",physical_dsi="NOT_RUN",retail_game="NOT_RUN",peer_timeout_032="OPEN",official_awards=0),indent=2))
def zipdir(folder,dest):
    with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts:z.write(p,p.relative_to(folder).as_posix())
(stage/"SHA256SUMS.txt").write_text("\n".join(hashlib.sha256(f.read_bytes()).hexdigest()+"  "+f.relative_to(stage).as_posix() for f in sorted(stage.rglob("*")) if f.is_file())+"\n")
zipdir(stage,out/"DSi_RA_Bridge_SD_033_EMULATOR_VALIDATED_PHYSICAL_NOT_RUN.zip")
# Corresponding source: exact complete upstream bootloader plus modification script;
# generated post-patch sources and load.bin are additionally included from build.
with zipfile.ZipFile(out/"DSi_RA_Bridge_033_Corresponding_Source.zip","w",zipfile.ZIP_DEFLATED) as z:
    for folder in ["dsi/launcher-033-gpl","dsi/fixture-033","dsi/observer-033","scripts","windows/observer-033","tests","docs"]:
        for f in sorted((root/folder).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:z.write(f,f.relative_to(root).as_posix())
    for f in sorted((root/"third_party/nds-bootloader").rglob("*")):
        if f.is_file() and ".git" not in f.parts:z.write(f,f.relative_to(root).as_posix())
    for f in sorted((build/"loader-source").rglob("*")):
        if f.is_file():z.write(f,"built-loader/"+f.relative_to(build/"loader-source").as_posix())
    for f in ["load_bin.c","load_bin.h"]:z.write(build/"generated"/f,"dsi/launcher-033-gpl/source/"+f)
    z.write(build/"instrumented/expected.h","dsi/launcher-033-gpl/source/expected.h")
    z.write(build/"instrumented/instrumentation.json","instrumentation.json")
    for f in ["Makefile","load.ld","load.bin"]:z.write(build/f,"built-loader/"+f)
    for f in ["LICENSE","THIRD_PARTY_033.md",".github/workflows/independent-observer-033.yml"]:z.write(root/f,f)

print(json.dumps(dict(status="PASS",physical="NOT_RUN",files=[p.name for p in out.glob("*033*.zip")])))
