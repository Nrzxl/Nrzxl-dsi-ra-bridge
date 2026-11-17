"""Conformance against published DS hash components using only synthetic data."""
import sys,tempfile,subprocess,hashlib,struct,json
from pathlib import Path
exe=str(Path(sys.argv[1]).resolve())
with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/"owned-fixture.nds";b=bytearray(0x3000)
    struct.pack_into("<I",b,0x20,0x200);struct.pack_into("<I",b,0x2c,0x100)
    struct.pack_into("<I",b,0x30,0x400);struct.pack_into("<I",b,0x3c,0x100);struct.pack_into("<I",b,0x68,0x1000)
    b[0x200:0x300]=bytes(range(256));b[0x400:0x500]=bytes(reversed(range(256)))
    expected=hashlib.md5(b[:0x160]+b[0x200:0x300]+b[0x400:0x500]+b[0x1000:0x1a00]).hexdigest()
    def run():
        path.write_bytes(b);r=subprocess.run([exe,str(path)],text=True,capture_output=True,check=True);return json.loads(r.stdout)
    r=run();assert r["hash"]==expected and not r["game_resolved"] and not r["submitted"]
    assert r["hash"]!=hashlib.md5(b).hexdigest()
    b[0x2900]=99;assert run()["hash"]==expected
    b[0x201]^=1;assert run()["hash"]!=expected
    path.write_bytes(b[:512]);assert subprocess.run([exe,str(path)],capture_output=True).returncode!=0
print(json.dumps(dict(status="PASS",scope="official DS hash, synthetic component conformance and bounds",checks=5)))
