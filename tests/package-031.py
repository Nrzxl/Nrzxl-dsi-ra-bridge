"""Verify the actual deliverable ZIP, manifest and every listed SHA256."""
import hashlib, json, sys, zipfile
from pathlib import PurePosixPath
archive = sys.argv[1]
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert len(names) == len(set(names))
    for name in names:
        p = PurePosixPath(name)
        assert not p.is_absolute() and ".." not in p.parts
        assert name != "boot.nds" and not name.startswith(("private/", "_nds/"))
    manifest = json.loads(z.read("manifest.json"))
    assert manifest["version"] == "0.3.1"
    assert manifest["physical_dsi"] == "NOT_RUN"
    count = 0
    for line in z.read("SHA256SUMS.txt").decode().splitlines():
        digest, name = line.split("  ", 1)
        assert hashlib.sha256(z.read(name)).hexdigest() == digest, name
        count += 1
    assert count == len(names) - 1  # every entry except the sums file itself
print(json.dumps(dict(status="PASS", zip=archive, verified_hashes=count,
                      manifest=True, archive_integrity=True, physical031="NOT_RUN")));
