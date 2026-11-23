#!/usr/bin/env python3
"""DSi RA Bridge 0.4.5: offline, metadata-safe coverage inventory for RA game 9983.

Uses ONLY the official RA GetGameExtended v1 metadata (file or a single HTTPS
request with RA_WEB_API_KEY from the local environment). This API returns the
MD5 of achievement logic in "MemAddr", NOT executable triggers.

Optionally accept an authorized local game-patch export to INDEX raw trigger
address references; this is static syntax inventory, NOT rcheevos evaluation.
Never commit or upload the unredacted export, API key, ROM, save, or memory dump.
No live awards, logins, emulation or network calls to award endpoints.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

GAME_ID = 9983
GAME_HASH_ASMP_EU = "ba3c4052e00c5cc31df5d5534c39de1b"
CORE_CATEGORIES = {
    "stars": r"\b(?:stars?|star[ -]coins?|silver stars?)\b",
    "coins": r"\b(?:coins?|red coins?|blue coins?)\b",
    "lives_health": r"\b(?:lives|life|health|damage|damaged|hurt|dying|died|death|deaths|1[ -]?up|hitless)\b",
    "time_speed": r"\b(?:time|timed|seconds?|minutes?|within \d+|under \d+|fastest|speed|speedy|race|racing|clock|timer|quick)\b",
    "stages_bosses": r"\b(?:level|stage|course|world|area|boss|bowser|fortress|castle|island|mountain|land|mission)\b",
    "characters": r"\b(?:mario|luigi|yoshi|wario|character|cap|transformation|metal|wing|invisible)\b",
    "minigames": r"\b(?:minigame|mini[ -]?game|rec room|shuffle shell|puzzle|memory match|trampoline|wanted!|bounce and trounce)\b",
    "score_records": r"\b(?:score|points?|record|combo|streak|leaderboard)\b",
    "progress_flags": r"\b(?:unlock|door|key|switch|activate|complete|collect|obtain|rabbit|cannon|open|finish|defeat)\b",
    "restrictions": r"\b(?:without|never|do not|don't|only|no damage|no caps|in a single session|without dying)\b",
}
PATTERNS = {k: re.compile(v, re.I) for k, v in CORE_CATEGORIES.items()}
HEX32 = re.compile(r"^[0-9a-fA-F]{32}$")
# Recognize ordinary rcheevos memory references only. This is not an RA
# expression parser: AddAddress, pointer chains, indirect offsets, recall,
# trigger modifiers and alternative groups still need rcheevos itself.
MEM_REF = re.compile(r"(?<![A-Za-z0-9_])0x(?:[HMLUSTWXNOKQ])?([0-9a-fA-F]{1,8})\b")
FORBIDDEN_OUTPUT_KEYS = {"token", "password", "apikey", "api_key", "username", "user", "email", "authorization", "cookie"}

def fail(message):
    raise ValueError(message)

def int_id(value, label):
    if isinstance(value, bool):
        fail(label + " invalid")
    try:
        number = int(value)
    except (TypeError, ValueError):
        fail(label + " missing or invalid")
    if number < 1:
        fail(label + " must be positive")
    return number

def parse_json_file(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 12_000_000:
        fail("JSON input absent or above 12 MB (refusing unsafe input)")
    with p.open("r", encoding="utf-8-sig") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        fail("Top-level JSON object required")
    return obj

def fetch_public_metadata():
    key = os.environ.get("RA_WEB_API_KEY", "").strip()
    if not key:
        fail("RA_WEB_API_KEY must be set locally; never paste keys into chat/GitHub")
    url = "https://retroachievements.org/API/API_GetGameExtended.php?" + urllib.parse.urlencode(
        {"y": key, "i": GAME_ID, "f": 3}
    )
    # An HTTP exception may include the API key in its URL; NEVER propagate it.
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DSiRABridge-045-LocalCoverage/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read(8_000_001)
        if len(data) > 8_000_000:
            fail("Metadata response too large")
        return json.loads(data.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, UnicodeError, json.JSONDecodeError) as e:
        if isinstance(e, urllib.error.HTTPError):
            fail("RA metadata HTTP status %d" % e.code)
        fail("RA metadata request failed (no credentials or URLs are logged)")

def classify(title, description):
    text = (title + " " + description).lower()
    matches = [k for k, pattern in PATTERNS.items() if pattern.search(text)]
    return matches or ["uncategorized"]

def game_id(obj):
    for field in ("ID", "GameId", "GameID", "gameId", "id"):
        if field in obj:
            return int_id(obj[field], "Game ID")
    fail("Game ID missing; refuse ambiguous set")

def elements(obj, field):
    val = obj.get(field)
    if isinstance(val, dict):
        return list(val.values())
    if isinstance(val, list):
        return val
    fail("%s missing or unsupported" % field)

def achievements_from_metadata(metadata):
    if game_id(metadata) != GAME_ID:
        fail("Metadata game ID mismatch (expected %d)" % GAME_ID)
    raw = elements(metadata, "Achievements")
    if not 0 < len(raw) <= 2500:
        fail("Metadata achievement count out of bounds")
    achievements = {}
    for a in raw:
        if not isinstance(a, dict):
            fail("Malformed achievement")
        aid = int_id(a.get("ID", a.get("id")), "Achievement ID")
        if aid in achievements:
            fail("Duplicate achievement ID %s" % aid)
        title = str(a.get("Title", a.get("title", ""))).strip()[:200]
        description = str(a.get("Description", a.get("description", ""))).strip()[:500]
        if not title or not description:
            fail("Achievement metadata incomplete for ID %s" % aid)
        memaddr = a.get("MemAddr", a.get("memAddr", ""))
        if memaddr is None:
            memaddr = ""
        if not isinstance(memaddr, str) or (memaddr and not HEX32.fullmatch(memaddr)):
            fail("Metadata MemAddr is not an MD5 digest; never interpret it as logic")
        achievements[aid] = {
            "id": aid,
            "title": title,
            "description": description,
            "categories": classify(title, description),
            "logic_md5": memaddr.lower() if memaddr else None,
            "points": int(a.get("Points", a.get("points", 0)) or 0),
            "trigger_status": "NO_RAW_CONDITIONS",
        }
    return achievements

def patch_achievements(patch):
    """Index an already authorized local export, never fetch/login with this tool."""
    if "PatchData" in patch:
        patch = patch["PatchData"]
    if not isinstance(patch, dict) or game_id(patch) != GAME_ID:
        fail("Authorized patch GameId mismatch")
    sets = patch.get("Sets")
    if not isinstance(sets, list) or not sets:
        fail("Authorized patch must contain Sets[]")
    a = {}
    for block in sets:
        if not isinstance(block, dict):
            fail("Malformed set in authorized patch")
        entries = elements(block, "Achievements")
        for x in entries:
            if not isinstance(x, dict):
                fail("Malformed patch achievement")
            aid = int_id(x.get("ID"), "Patch achievement ID")
            if aid in a:
                fail("Duplicate patch achievement ID %d" % aid)
            trigger = x.get("MemAddr")
            if not isinstance(trigger, str) or not trigger or HEX32.fullmatch(trigger):
                fail("Patch trigger for %d absent or hashed; cannot use MD5 as logic" % aid)
            if len(trigger) > 30000:
                fail("Trigger above 30k chars")
            # Do not distribute raw authored logic; keep only address references.
            addrs = [int(h, 16) for h in MEM_REF.findall(trigger)]
            main = sorted({n for n in addrs if 0 <= n < 0x400000})
            dtcm = sorted({n for n in addrs if 0x1000000 <= n < 0x1004000})
            other = sorted({n for n in addrs if n >= 0x400000 and not (0x1000000 <= n < 0x1004000)})
            a[aid] = {
                "id": aid,
                "referenced_addresses": len(set(addrs)),
                "main_ram_offsets": main,
                "dtcm_offsets": dtcm,
                "out_of_memory_map_offsets": other,
                "triggers_indexed": bool(addrs),
                "notes": "Syntax-only; pointer expressions/temporal hits need rcheevos evaluation",
            }
    return a

def report(metadata, patch=None):
    ach = achievements_from_metadata(metadata)
    cat = Counter()
    for a in ach.values():
        for key in a["categories"]:
            cat[key] += 1
    patched = patch_achievements(patch) if patch is not None else {}
    covered = sorted(set(ach) & set(patched))
    orphan = sorted(set(patched) - set(ach))
    missing = sorted(set(ach) - set(patched))
    addresses_main, addresses_dtcm, unsupported = set(), set(), set()
    raw_indexed = 0
    for aid in covered:
        item = patched[aid]
        addresses_main.update(item["main_ram_offsets"])
        addresses_dtcm.update(item["dtcm_offsets"])
        unsupported.update(item["out_of_memory_map_offsets"])
        ach[aid]["trigger_status"] = "SYNTAX_INDEXED_NOT_EVALUATED" if item["triggers_indexed"] else "UNPARSED_RAW_TRIGGER"
        ach[aid]["referenced_addresses"] = item["referenced_addresses"]
        raw_indexed += int(item["triggers_indexed"])
    canonical = [[x["id"], x["title"], x["description"], x["logic_md5"]] for x in sorted(ach.values(), key=lambda x: x["id"])]
    revision = hashlib.sha256(json.dumps(canonical, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()
    # All names/metadata refer to the official game, but classification is
    # keyword-derived and not an address map.
    result = {
        "format": "DSIRB045_RA_COVERAGE_REPORT_V1",
        "game_id": GAME_ID,
        "game_title": str(metadata.get("Title", "Super Mario 64 DS"))[:150],
        "expected_eu_ra_hash": GAME_HASH_ASMP_EU,
        "catalog_achievement_count": len(ach),
        "catalog_revision_sha256": revision,
        "catalog_source": "GetGameExtended metadata; no live credentials stored",
        "category_method": "keyword heuristic; categories overlap and are not RA predicates",
        "category_counts": {k: cat[k] for k in [*CORE_CATEGORIES, "uncategorized"]},
        "raw_trigger_index": {
            "source": "authorized local patch export" if patch is not None else "NONE",
            "metadata_entries_with_raw_patch": len(covered),
            "parsed_reference_entries": raw_indexed,
            "missing_raw_achievement_ids": missing,
            "patch_ids_not_in_catalog": orphan,
            "unique_main_ram_offsets": len(addresses_main),
            "unique_dtcm_offsets": len(addresses_dtcm),
            "unique_out_of_scope_offsets": len(unsupported),
            "out_of_scope_offsets_hex": ["0x%X" % n for n in sorted(unsupported)[:64]],
            "scope_note": "rcheevos expressions may include indirection; refs do NOT prove watched memory or evaluation",
        },
        "gates": {
            "official_metadata_indexed": True,
            "all_raw_trigger_definitions_indexed": len(covered) == len(ach) and raw_indexed == len(ach),
            "rcheevos_frames_evaluated_on_dsi": False,
            "achievement_conditions_validated_on_dsi": False,
            "official_awards_sent": False,
            "physical_045_tested": False,
            "note": "Only official rcheevos evaluation with a real set on DSi can validate gameplay predicates",
        },
        "achievements": [ach[k] for k in sorted(ach)],
    }
    result["status"] = ("TRIGGER_ADDRESSES_INDEXED_NOT_EVALUATED"
                        if patched else "OFFICIAL_METADATA_INDEXED_RAW_TRIGGERS_PENDING")
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--game-extended", type=Path, help="Local GetGameExtended JSON (no API key in file)")
    source.add_argument("--fetch-ra-api", action="store_true", help="Read RA_WEB_API_KEY from local environment, one HTTPS metadata request")
    parser.add_argument("--authorized-patch", type=Path, help="Optional already-authorized raw game patch JSON, read locally, never published")
    parser.add_argument("--out", required=True, type=Path, help="NEW sanitized report JSON path")
    args = parser.parse_args()
    try:
        if args.out.exists():
            fail("Report already exists; refusing overwrite")
        if args.out.parent == Path(".") and not args.out.parent.is_dir():
            fail("Output directory missing")
        metadata = fetch_public_metadata() if args.fetch_ra_api else parse_json_file(args.game_extended)
        patch = parse_json_file(args.authorized_patch) if args.authorized_patch else None
        result = report(metadata, patch)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # Sensitive fields are neither copied from metadata nor patch. Just
        # game metadata and aggregate refs are written.
        with args.out.open("x", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(json.dumps({
            "status": result["status"],
            "game_id": GAME_ID,
            "catalog_achievement_count": result["catalog_achievement_count"],
            "raw_triggers_indexed": result["raw_trigger_index"]["parsed_reference_entries"],
            "categories": result["category_counts"],
            "physical_045_tested": False,
            "official_awards_sent": False,
        }, ensure_ascii=False))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        # File/IO messages can leak input names but NEVER credentials or URLs.
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
