"""Package ONLY a real build whose validator report matches its SHA256."""
import argparse
import hashlib
import json
import shutil
import struct
import zipfile
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("out"))
    parser.add_argument("--commit", required=True)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    if len(args.commit) != 40 or any(c not in "0123456789abcdef" for c in args.commit):
        raise ValueError("Expected full source commit SHA")
    if not args.image.startswith("devkitpro/devkitarm@sha256:"):
        raise ValueError("Expected resolved official image digest")
    first = args.root / "first" / "DSiRABridge_Network_030.nds"
    second = args.root / "second" / first.name
    digest = sha(first)
    if digest != sha(second):
        raise ValueError("Reproducibility FAIL: NDS outputs differ")
    evidence = json.loads((args.root / "first" / "structure.json").read_text())
    if evidence.get("status") != "PASS" or evidence.get("sha256") != digest:
        raise ValueError("Missing/mismatched structure validation")
    elf = args.root / "first" / "DSiRABridge_Network_030.elf"
    header = elf.read_bytes()[:20]
    if header[:4] != b"\x7fELF" or header[4:6] != b"\x01\x01" or struct.unpack_from("<H", header, 18)[0] != 40:
        raise ValueError("Expected a real ELF32 little-endian ARM executable")
    stage = args.root / "DSi_RA_Bridge_SD_030"
    stage.mkdir(exist_ok=False)
    ndsdir = stage / "nds" / "DSiRABridge_030"
    ndsdir.mkdir(parents=True)
    shutil.copyfile(first, ndsdir / first.name)
    shutil.copyfile(Path("docs/sd-test-030.txt"), stage / "DSiRABridge_TEST.txt")
    licenses = args.root / "first" / "licenses"
    if licenses.exists():
        shutil.copytree(licenses, stage / "licenses")
    manifest = dict(version="0.3.0", source_commit=args.commit, image=args.image,
                    binary_sha256=digest, binary_bytes=first.stat().st_size,
                    arm_build="PASS", structure="PASS", reproducibility="PASS",
                    physical_dsi="NOT_RUN", persistent_monitor="NOT_RUN",
                    official_achievements="NOT_RUN", nand_writes="not implemented",
                    provenance="compiled artifact; hardware compatibility unvalidated")
    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    entries = sorted(p for p in stage.rglob("*") if p.is_file())
    sums = "".join(f"{sha(p)}  {p.relative_to(stage).as_posix()}\n" for p in entries)
    (stage / "SHA256SUMS.txt").write_text(sums, encoding="ascii")
    target = args.root / "DSi_RA_Bridge_SD_030_UNVALIDATED.zip"
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(p for p in stage.rglob("*") if p.is_file()):
            relative = p.relative_to(stage).as_posix()
            if relative == "boot.nds" or relative.startswith("private/") or ".." in relative.split("/"):
                raise ValueError("Unsafe SD path")
            item = zipfile.ZipInfo(relative, date_time=(2026, 11, 16, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, p.read_bytes())
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        name = "nds/DSiRABridge_030/" + first.name
        if hashlib.sha256(archive.read(name)).hexdigest() != digest:
            raise ValueError("ZIP binary mismatch")
    print(json.dumps(dict(zip=str(target), zip_sha256=sha(target), **manifest), indent=2))

if __name__ == "__main__":
    main()
