"""047: local-only raw-conditions manifest gate (synthetic fixtures ONLY)."""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("conditions_047", ROOT / "scripts/prepare-local-conditions-047.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def catalog():
    entries = [
        {"id": 11, "logic_md5": "a" * 32},
        {"id": 12, "logic_md5": "b" * 32},
    ]
    return {"format": module.FORMAT, "game_id": 9983,
            "catalog_revision_sha256": "c" * 64,
            "catalog_achievement_count": 2, "achievements": entries}

def patch():
    return {"PatchData": {"ID": 9983, "Sets": [
        {"Achievements": [{"ID": 11, "MemAddr": "0xH000100=1"}]},
        {"Achievements": [{"ID": 12, "MemAddr": "0xH000101=3"}]}
    ]}}

class Prepare047Test(unittest.TestCase):
    def test_real_manifest_local_only(self):
        body, active, total = module.prepare(catalog(), patch(), require_all=True)
        self.assertEqual(active, 2)
        self.assertEqual(total, 2)
        self.assertEqual(body, "DSIRB047\t9983\t%s\n11\t0xH000100=1\n12\t0xH000101=3\n" % ("c" * 64))

    def test_reject_missing_one_when_require_all(self):
        p = patch()
        p["PatchData"]["Sets"].pop()
        with self.assertRaisesRegex(module.Blocked, "incomplete"):
            module.prepare(catalog(), p, require_all=True)

    def test_allow_subset_if_explicit(self):
        p = patch()
        p["PatchData"]["Sets"].pop()
        body, active, total = module.prepare(catalog(), p, require_all=False)
        self.assertEqual((active,total), (1,2))
        self.assertNotIn("12\t", body)

    def test_wrong_game_rejected(self):
        p = patch()
        p["PatchData"]["ID"] = 9982
        with self.assertRaisesRegex(module.Blocked, "Game ID"):
            module.prepare(catalog(), p)

    def test_unknown_achievement_id_rejected(self):
        p = patch()
        p["PatchData"]["Sets"][0]["Achievements"][0]["ID"] = 13
        with self.assertRaisesRegex(module.Blocked, "missing from official"):
            module.prepare(catalog(), p)

    def test_refuses_md5_instead_of_raw(self):
        p = patch()
        p["PatchData"]["Sets"][0]["Achievements"][0]["MemAddr"] = "f" * 32
        with self.assertRaisesRegex(module.Blocked, "hashed"):
            module.prepare(catalog(), p)

    def test_refuses_duplicate_patch_ids(self):
        p = patch()
        p["PatchData"]["Sets"][1]["Achievements"][0]["ID"] = 11
        with self.assertRaisesRegex(module.Blocked, "Duplicate"):
            module.prepare(catalog(), p)

    def test_refuses_control_or_tab_and_newline(self):
        for expr in ("0xH100=1\tYES", "0xH100=1\nNEXT", "0xH100=1\r", "0xH100=1\\X"):
            p = patch()
            p["PatchData"]["Sets"][0]["Achievements"][0]["MemAddr"] = expr
            with self.assertRaisesRegex(module.Blocked, "unsafe|invalid"):
                module.prepare(catalog(), p)

    def test_refuses_invalid_catalog(self):
        c = catalog()
        c["catalog_revision_sha256"] = "invalid"
        with self.assertRaisesRegex(module.Blocked, "revision"):
            module.prepare(c, patch())

    def test_refuses_duplicate_catalog_ids(self):
        c = catalog()
        c["achievements"][1]["id"] = 11
        with self.assertRaisesRegex(module.Blocked, "uniqueness"):
            module.prepare(c, patch())

    def test_manifest_synthetic_has_only_fabricated_ids(self):
        text = module.synthetic_manifest()
        self.assertIn("SYNTHETIC_ONLY", text)
        self.assertIn("46001\t0xH000100=1", text)
        self.assertNotIn("91455", text)

    def test_cli_does_not_overwrite_or_emit_private_expressions(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            cat_path, patch_path, manifest = p/"catalog.json",p/"patch.json",p/"local-manifest.tsv"
            cat_path.write_text(json.dumps(catalog()), encoding="utf8")
            patch_path.write_text(json.dumps(patch()), encoding="utf8")
            old_argv = sys.argv
            out = io.StringIO()
            try:
                sys.argv = ["prog","--authorized-patch",str(patch_path),
                            "--catalog",str(cat_path), "--out",str(manifest),
                            "--require-all"]
                with contextlib.redirect_stdout(out):
                    module.main()
            finally:
                sys.argv = old_argv
            info = json.loads(out.getvalue())
            self.assertEqual(info["status"],"LOCAL_MANIFEST_PREPARED")
            self.assertTrue(info["raw_conditions_inside_file"])
            self.assertFalse(info["official_awards_sent"])
            self.assertNotIn("0xH000100=1",out.getvalue())
            self.assertIn("11\t0xH000100=1",manifest.read_text())
            if os.name != "nt":
                self.assertEqual(manifest.stat().st_mode & 0o077,0)
            old_argv = sys.argv
            try:
                sys.argv = ["prog","--authorized-patch",str(patch_path),
                            "--catalog",str(cat_path), "--out",str(manifest)]
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    module.main()
            finally:
                sys.argv = old_argv

    def test_input_limit(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"big.json"
            p.write_bytes(b"x" * 12_000_001)
            with self.assertRaisesRegex(module.Blocked, "too large"):
                module.load(p)

if __name__ == "__main__":
    unittest.main(verbosity=2)
