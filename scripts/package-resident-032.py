"""Separate cooperative module PoC package, gated by actual ARM CPU test results."""
import hashlib, json, struct, zlib, zipfile
from pathlib import Path
out = Path("out")
first, second = out/"resident-first", out/"resident-second"
binary = first/"DSiRABridge_Resident_032.nds"
payload = (first/"payload.bin").read_bytes()
assert binary.read_bytes() == (second/binary.name).read_bytes()
assert payload == (second/"payload.bin").read_bytes() and 0 < len(payload) <= 4096
test = [json.loads(x) for x in (out/"logs/resident-unicorn.jsonl").read_text().splitlines() if x.strip().startswith("{")]
assert len(test) == 2 and all(x["status"] == "PASS" and x["frames"] == 6000 for x in test)
structure = json.loads((first/"structure.json").read_text())
assert structure["status"] == "PASS"
assert structure["sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()
dsb = b"DSBP" + struct.pack("<7I", 1, len(payload), zlib.crc32(payload), 1, 0, 0, 0) + payload
entries = {
 "nds/DSiRABridge_032_Resident/"+binary.name:binary.read_bytes(),
 "DSiRABridge_032_Resident/payload.dsb":dsb,
 "RESIDENT_032_READ_FIRST.md":Path("docs/resident-032.md").read_bytes(),
 "LICENSE":Path("LICENSE").read_bytes(),
}
for item in (out/"first/licenses").rglob("*"):
 if item.is_file(): entries["licenses/"+item.relative_to(out/"first/licenses").as_posix()] = item.read_bytes()
manifest = dict(version="0.3.2",scope="A homebrew plus cooperative ARM module B; NOT a second NDS loader",
 arm_build="PASS",cpu_simulation="PASS",physical_dsi="NOT_RUN",source_commit=__import__("os").environ["GITHUB_SHA"],
 official_submissions=0,nand_writes=False,unlaunch_required=False,
 binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),payload_sha256=hashlib.sha256(dsb).hexdigest())
entries["manifest.json"] = json.dumps(manifest,indent=2).encode()
entries["SHA256SUMS.txt"] = "".join(hashlib.sha256(data).hexdigest()+"  "+name+"\n" for name,data in sorted(entries.items())).encode()
target=out/"DSi_RA_Bridge_Resident_PoC_032_CPU_ONLY.zip"
with zipfile.ZipFile(target,"x",zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted(entries.items()): z.writestr(name,data)
print(json.dumps(dict(zip=str(target),zip_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),**manifest)))
