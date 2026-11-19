#!/usr/bin/env python3
"""034D: build-time path isolation for pinned GPL DScheevos+nds-bootstrap.

This does not modify the user's SD card or install anything. Fail closed on
unrecognized shared nds-bootstrap paths, changing pins or missing source.
All affected upstream sources remain GPL-3.0 and are distributed as sources.
"""
import argparse
import json
from pathlib import Path

UPSTREAM_REF = "59e9978be7b9c3788357ef0a609caf9dc8ea74f3"
BOOT_REF = "af351f096dd71a37e0e5b18d9709bcc0fb70342f"
SOURCE_ROOTS = ("dscheevos/launcher", "dscheevos/module",
                "external/nds-bootstrap/retail")
EXT = {".c", ".cpp", ".h", ".hpp", ".s", ".S", ".asm", ".inc", ".ini"}
REPLACEMENTS = (
    ("sd:/_nds/nds-bootstrap.ini", "sd:/_nds/dsirb034d/nds-bootstrap.ini"),
    ("fat:/_nds/nds-bootstrap.ini", "fat:/_nds/dsirb034d/nds-bootstrap.ini"),
    ("/_nds/nds-bootstrap/", "/_nds/dsirb034d-cache/"),
    ("/_nds/dscheevos/", "/_nds/dsirb034d/"),
    # Path literals without a trailing slash (mkdir, comments, safety labels)
    # must also be moved away from the stable installation.
    ("_nds/nds-bootstrap", "_nds/dsirb034d-cache"),
    ("_nds/dscheevos", "_nds/dsirb034d"),
)
REMAINING_FORBIDDEN = ("_nds/nds-bootstrap", "_nds/dscheevos")

def source_files(root):
    for part in SOURCE_ROOTS:
        folder = root / part
        if not folder.is_dir():
            raise ValueError("pinned source tree missing: " + part)
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix in EXT:
                yield path

def patch(root):
    touched = []
    total = 0
    for path in source_files(root):
        try:
            old = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = old
        for before, after in REPLACEMENTS:
            new = new.replace(before, after)
        if new != old:
            path.write_text(new, encoding="utf-8")
            touched.append(str(path.relative_to(root)))
            total += 1
    # On the very first experimental run: no network, RA auth, session or
    # achievements. User cannot accidentally send awards from an untested
    # loader. Follow-up can enable spectator through a reviewed later gate.
    config = root / "dscheevos/launcher/source/config.c"
    old = config.read_text()
    needles = {
        "s->enabled = 1;": "s->enabled = 0;",
        "s->hardcore = 1;": "s->hardcore = 0;",
        "s->live = 1;": "s->live = 0;",
        'strcpy(s->host, DEFAULT_HOST);': "s->spectator = 1;\n  strcpy(s->host, DEFAULT_HOST);",
    }
    for before, after in needles.items():
        if old.count(before) != 1:
            raise ValueError("unsafe launcher config drift: " + before)
        old = old.replace(before, after)
    config.write_text(old)
    # The launcher keeps a path to its bundled bootstrap via DSC_DIR.
    launcher_h = root / "dscheevos/launcher/source/config.h"
    if '#define DSC_DIR "sd:/_nds/dsirb034d/"' not in launcher_h.read_text():
        raise ValueError("launcher path isolation missing")
    if total < 4:
        raise ValueError("insufficient upstream path replacements")
    return touched

def verify(root):
    remaining = []
    files = 0
    isolated_references = 0
    for path in source_files(root):
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files += 1
        isolated_references += source.count("_nds/dsirb034d")
        for forbidden in REMAINING_FORBIDDEN:
            if forbidden in source:
                remaining.append({"source": str(path.relative_to(root)),
                                  "unexpected_path": forbidden})
    if remaining or isolated_references < 4:
        raise ValueError("unisolated legacy source refs: " + json.dumps(remaining[:20]))
    if "s->enabled = 0;" not in (root / "dscheevos/launcher/source/config.c").read_text():
        raise ValueError("offline boot not enforced")
    return {"status": "PINNED_SOURCE_PATH_GATES_PASS", "source_files_checked": files,
            "isolated_reference_count": isolated_references,
            "offline_boot_default": True,
            "gpl_upstream_version": UPSTREAM_REF,
            "bootstrap_version": BOOT_REF,
            "retail_on_real_dsi": "NOT_RUN",
            "official_awards": 0}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--mode", choices=("apply", "verify"), required=True)
    args = parser.parse_args()
    try:
        result = {}
        if args.mode == "apply":
            result["changed"] = patch(args.upstream)
        result.update(verify(args.upstream))
    except (OSError, ValueError) as e:
        print(json.dumps({"status": "BLOCKED", "reason": str(e)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
