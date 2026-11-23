"""Synthetic-only regression suite for 045 RA official-set coverage inventory."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("coverage045", ROOT / "scripts/ra-set-coverage-045.py")
cover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cover)

def sample():
    return {
        "ID": 9983, "Title": "Super Mario 64 DS", "Achievements": {
            "10": {"ID": 10, "Title": "Star Collecting", "Description": "Collect 80 Power Stars", "Points": 5, "MemAddr": "a"*32},
            "11": {"ID": 11, "Title": "No Damage", "Description": "Finish a stage without taking damage", "Points": 10, "MemAddr": "b"*32},
            "12": {"ID": 12, "Title": "Speed Run", "Description": "Finish within 40 seconds, collect silver coins", "Points": 5, "MemAddr": "c"*32},
            "13": {"ID": 13, "Title": "Puzzle Game", "Description": "Earn 25 points in a minigame", "Points": 1, "MemAddr": "d"*32},
            "14": {"ID": 14, "Title": "Secret Thing", "Description": "Do something secret", "Points": 1, "MemAddr": "e"*32},
        },
        "user": "SHOULD_NEVER_OUTPUT", "token": "TOP_SECRET",
    }

def patch():
    return {"Success": True, "PatchData": {"GameId": 9983, "Sets": [{"Achievements": [
        {"ID": 10, "MemAddr": "0xH000123=5_R:0xX000200>0"},
        {"ID": 11, "MemAddr": "0xH1000020=1_0xH400010=0"},
        {"ID": 12, "MemAddr": "0xH000456=8"},
    ]}]}}

class Coverage045(unittest.TestCase):
    def test_index_no_raw_logic_from_md5(self):
        r = cover.report(sample())
        self.assertEqual(r["status"], "OFFICIAL_METADATA_INDEXED_RAW_TRIGGERS_PENDING")
        self.assertEqual(r["catalog_achievement_count"], 5)
        self.assertEqual(r["raw_trigger_index"]["parsed_reference_entries"], 0)
        self.assertFalse(r["gates"]["all_raw_trigger_definitions_indexed"])
        self.assertFalse(r["gates"]["official_awards_sent"])
        self.assertFalse(r["gates"]["physical_045_tested"])
        self.assertIn("stars", r["achievements"][0]["categories"])
        self.assertIn("uncategorized", r["achievements"][4]["categories"])

    def test_coverage_categories_overlap_and_time(self):
        r = cover.report(sample())
        self.assertEqual(r["category_counts"]["time_speed"], 1)
        self.assertEqual(r["category_counts"]["coins"], 1)
        self.assertEqual(r["category_counts"]["minigames"], 1)
        self.assertEqual(r["category_counts"]["lives_health"], 1)
        self.assertGreaterEqual(r["category_counts"]["restrictions"], 1)

    def test_raw_patch_index_is_syntax_only(self):
        r = cover.report(sample(), patch())
        x = r["raw_trigger_index"]
        self.assertEqual(x["metadata_entries_with_raw_patch"], 3)
        self.assertEqual(x["parsed_reference_entries"], 3)
        self.assertEqual(x["unique_main_ram_offsets"], 3)
        self.assertEqual(x["unique_dtcm_offsets"], 1)
        self.assertEqual(x["unique_out_of_scope_offsets"], 1)
        self.assertEqual(x["missing_raw_achievement_ids"], [13, 14])
        self.assertFalse(r["gates"]["all_raw_trigger_definitions_indexed"])
        self.assertFalse(r["gates"]["rcheevos_frames_evaluated_on_dsi"])
        self.assertFalse(r["gates"]["achievement_conditions_validated_on_dsi"])

    def test_all_synthetic_conditions_indexed_but_not_evaluated(self):
        s = sample()
        p = {"GameId": 9983, "Sets": [{"Achievements": [
            {"ID": int(k), "MemAddr": "0xH000012=0"}
            for k in s["Achievements"]
        ]}]}
        r = cover.report(s, p)
        self.assertTrue(r["gates"]["all_raw_trigger_definitions_indexed"])
        self.assertFalse(r["gates"]["achievement_conditions_validated_on_dsi"])
        self.assertFalse(r["gates"]["official_awards_sent"])

    def test_never_expose_user_api_or_patch_token(self):
        p = patch()
        p["PatchData"]["token"] = "CUSTOM_SECRET"
        r = cover.report(sample(), p)
        blob = json.dumps(r)
        self.assertNotIn("CUSTOM_SECRET", blob)
        self.assertNotIn("TOP_SECRET", blob)
        self.assertNotIn("SHOULD_NEVER_OUTPUT", blob)

    def test_patch_md5_cannot_be_used_as_trigger(self):
        p = patch()
        p["PatchData"]["Sets"][0]["Achievements"][0]["MemAddr"] = "3"*32
        with self.assertRaisesRegex(ValueError, "hashed"):
            cover.report(sample(), p)

    def test_game_id_mismatch_fails_closed(self):
        s = sample()
        s["ID"] = 8888
        with self.assertRaisesRegex(ValueError, "mismatch"):
            cover.report(s)
        p = patch()
        p["PatchData"]["GameId"] = 1111
        with self.assertRaisesRegex(ValueError, "mismatch"):
            cover.report(sample(), p)

    def test_duplicates_and_missing_metadata_fail(self):
        s = sample()
        s["Achievements"] = [s["Achievements"]["10"], s["Achievements"]["10"]]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            cover.report(s)
        s = sample()
        del s["Achievements"]["11"]["Description"]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            cover.report(s)

    def test_report_revision_is_deterministic_and_revision_sensitive(self):
        a = cover.report(sample())
        b = cover.report(sample())
        self.assertEqual(a["catalog_revision_sha256"], b["catalog_revision_sha256"])
        s = sample()
        s["Achievements"]["10"]["Description"] += " without dying"
        c = cover.report(s)
        self.assertNotEqual(a["catalog_revision_sha256"], c["catalog_revision_sha256"])

    def test_local_file_parser_size_and_object_guards(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.json"
            p.write_text(json.dumps(sample()), encoding="utf-8")
            self.assertEqual(cover.parse_json_file(p)["ID"], 9983)
            p.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Top-level"):
                cover.parse_json_file(p)

    def test_unmapped_conditions_do_not_falsely_claim_ram_support(self):
        s = sample()
        p = {"GameId": 9983, "Sets": [{"Achievements": [
            {"ID": 10, "MemAddr": "0xHFFFFFFF=1"},
        ]}]}
        r = cover.report(s, p)
        self.assertEqual(r["raw_trigger_index"]["unique_out_of_scope_offsets"], 1)
        self.assertFalse(r["gates"]["all_raw_trigger_definitions_indexed"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
