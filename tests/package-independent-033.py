"""Checks the actual deliverable; refuses an EMU_ONLY launcher in the physical SD ZIP."""
import zipfile,hashlib,json,sys
from pathlib import PurePosixPath
path=sys.argv[1]
with zipfile.ZipFile(path) as z:
    names=z.namelist();assert len(names)==len(set(names))
    for name in names:
        p=PurePosixPath(name)
        assert not p.is_absolute() and ".." not in p.parts and "\\" not in name
        assert not any(x.lower() in ("private","boot.nds","_nds","saves") for x in p.parts)
        assert "EMU_ONLY" not in name
    expected={"nds/DSiRABridge_033/Launcher_A_033.nds","nds/DSiRABridge_033/Fixture_B_033_control.nds","DSiRABridge_033/Fixture_B_033_observed.nds"}
    assert {n for n in names if n.lower().endswith(".nds")}==expected
    status=json.loads(z.read("STATUS.json"));assert status["physical_dsi"]=="NOT_RUN" and status["peer_timeout_032"]=="OPEN" and status["official_awards"]==0
    for row in z.read("SHA256SUMS.txt").decode().splitlines():
        digest,name=row.split("  ",1);assert hashlib.sha256(z.read(name)).hexdigest()==digest
    assert b"GNU GENERAL PUBLIC LICENSE" in z.read("licenses/launcher-GPL-2.txt")
print(json.dumps(dict(status="PASS",scope="actual SD033 ZIP, additive paths, provenance, licenses, hashes",nds_files=3)))
