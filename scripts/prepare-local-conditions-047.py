#!/usr/bin/env python3
"""DSi RA Bridge 047: prepare private *local* raw-trigger manifest for rcheevos.

No network calls. Never commit/share the raw authorized patch or manifest.
The output contains authored achievement logic as plaintext; keep it local.
The public GetGameExtended MemAddr MD5 is NEVER accepted as an expression.
"""
import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path

GAME_ID = 9983
FORMAT = "DSIRB045_RA_COVERAGE_REPORT_V1"
HEX32 = re.compile(r"^[a-fA-F0-9]{32}$")
HEX64 = re.compile(r"^[a-fA-F0-9]{64}$")
GOOD = re.compile(r"^[\x21-\x7e]{1,30000}$")


class Blocked(ValueError):
    pass


def load(path):
    if not path.is_file() or path.stat().st_size > 12_000_000:
        raise Blocked("Input missing or too large (>12MB)")
    with path.open("r", encoding="utf-8-sig") as f:
        result = json.load(f)
    if not isinstance(result, dict):
        raise Blocked("JSON object expected")
    return result


def int_id(item):
    if isinstance(item, bool):
        raise Blocked("Achievement ID invalid")
    try:
        number = int(item)
    except (ValueError, TypeError):
        raise Blocked("Achievement ID invalid")
    if not 1 <= number <= 0xffffffff:
        raise Blocked("Achievement ID out of range")
    return number


def entries(data):
    if isinstance(data, dict):
        return list(data.values())
    if isinstance(data, list):
        return data
    raise Blocked("Achievements list/dict required")


def extract_patch(patch):
    if "PatchData" in patch:
        patch = patch["PatchData"]
    if not isinstance(patch, dict) or int_id(patch.get("ID", patch.get("GameId"))) != GAME_ID:
        raise Blocked("Authorized patch Game ID is not 9983")
    sets = patch.get("Sets")
    if not isinstance(sets, list) or not sets:
        raise Blocked("Authorized patch must contain nonempty Sets[]")
    result = {}
    for block in sets:
        if not isinstance(block, dict):
            raise Blocked("Malformed set")
        for item in entries(block.get("Achievements")):
            if not isinstance(item, dict):
                raise Blocked("Malformed achievement")
            aid = int_id(item.get("ID"))
            expr = item.get("MemAddr")
            if aid in result:
                raise Blocked("Duplicate patch ID")
            if not isinstance(expr, str) or HEX32.fullmatch(expr) or not GOOD.fullmatch(expr):
                raise Blocked("Missing, hashed, or invalid raw expression")
            # Reject control characters, whitespace, and TSV/log injection.
            if any(c in expr for c in ("\t", "\r", "\n", "\\")):
                raise Blocked("Raw expression includes unsafe separator/escape")
            result[aid] = expr
    return result


def checked_catalog(catalog):
    if catalog.get("format") != FORMAT or catalog.get("game_id") != GAME_ID:
        raise Blocked("Expected official sanitized RA #9983 catalog (045)")
    revision = catalog.get("catalog_revision_sha256")
    if not isinstance(revision, str) or not HEX64.fullmatch(revision):
        raise Blocked("Catalog revision SHA256 invalid")
    rows = catalog.get("achievements")
    if not isinstance(rows, list) or not rows or len(rows) > 2500:
        raise Blocked("Catalog achievements absent")
    ids = []
    for item in rows:
        if not isinstance(item, dict):
            raise Blocked("Malformed catalog achievement")
        aid = int_id(item.get("id"))
        digest = item.get("logic_md5")
        if not isinstance(digest, str) or not HEX32.fullmatch(digest):
            raise Blocked("Missing/non-MD5 catalog digest")
        ids.append(aid)
    if len(set(ids)) != len(ids) or catalog.get("catalog_achievement_count") != len(ids):
        raise Blocked("Catalog ID count or uniqueness mismatch")
    return sorted(ids), revision.lower()


def prepare(catalog, patch, require_all=False):
    ids, revision = checked_catalog(catalog)
    expressions = extract_patch(patch)
    unknown = set(expressions) - set(ids)
    missing = set(ids) - set(expressions)
    if unknown:
        raise Blocked("Patch contains IDs missing from official catalog")
    if require_all and missing:
        raise Blocked("Patch is incomplete: does not include all catalog IDs")
    if not expressions:
        raise Blocked("No usable raw conditions")
    out = "DSIRB047\t%d\t%s\n" % (GAME_ID, revision)
    out += "".join("%d\t%s\n" % (aid, expressions[aid]) for aid in sorted(expressions))
    return out, len(expressions), len(ids)


def synthetic_manifest():
    return ("DSIRB047\t9983\tSYNTHETIC_ONLY\n"
            "46001\t0xH000100=1\n"
            "46002\t0xH000101=3\n"
            "46003\t0xH000102=55\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    selector = ap.add_mutually_exclusive_group(required=True)
    selector.add_argument("--synthetic", action="store_true",
                          help="Create synthetic-only manifest with invented QA conditions")
    selector.add_argument("--authorized-patch", type=Path,
                          help="Local user-authorized private raw game patch, never upload")
    ap.add_argument("--catalog", type=Path, help="045 sanitized catalog JSON (required for authorized-patch)")
    ap.add_argument("--require-all", action="store_true", help="Reject any absent catalog achievement")
    ap.add_argument("--out", required=True, type=Path, help="New local manifest; PLAINTEXT RAW CONDITIONS")
    args = ap.parse_args()
    try:
        if args.out.exists():
            raise Blocked("Refusing to overwrite an existing file")
        if args.synthetic:
            if args.catalog or args.require_all:
                raise Blocked("Synthetic demo takes neither --catalog nor --require-all")
            body, active, total = synthetic_manifest(), 3, 3
            mode = "SYNTHETIC"
        else:
            if args.catalog is None:
                raise Blocked("--catalog is required with --authorized-patch")
            body, active, total = prepare(load(args.catalog), load(args.authorized_patch), args.require_all)
            mode = "PRIVATE_AUTHORIZED_LOCAL"
        # Do not display expressions or write them to CI logs.
        args.out.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(str(args.out), flags, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="ascii", newline="\n") as f:
            f.write(body)
        if os.name != "nt":
            args.out.chmod(0o600)
        print(json.dumps({"status": "LOCAL_MANIFEST_PREPARED",
                          "mode": mode, "entries": active, "catalog_entries": total,
                          "raw_conditions_inside_file": True,
                          "official_awards_sent": False,
                          "warning": "PRIVATE PLAINTEXT: do not upload to chat/GitHub"}))
    except (OSError, Blocked, json.JSONDecodeError, UnicodeError) as exc:
        # Errors should never show raw conditions, tokens, or contents.
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
