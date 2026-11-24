"""048: synthetic PC RAM research tests (never using a user's ROM)."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    x = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = x
    spec.loader.exec_module(x)
    return x


d = load("ra_diff_048", "scripts/analyze-asmp-ram-048.py")
s = load("ra_fixture_048", "scripts/synthetic-asmp-captures-048.py")


def paths(directory):
    return tuple(directory / (s.STEM + "_" + x + ".bin") for x in ("before", "idle", "after"))


class Analyzer048Tests(unittest.TestCase):
    def test_eu_literature_address_grounding(self):
        self.assertEqual(d.EU_REFERENCE[0x09F2F4][0], "lives")
        self.assertEqual(d.EU_REFERENCE[0x11117C][0], "health_candidate_a")
        self.assertEqual(d.EU_REFERENCE[0x092144][0], "health_candidate_b")
        self.assertEqual(d.EU_REFERENCE[0x09F2F8][0], "level_id")

    def test_coin_expected_delta(self):
        a = bytearray(d.SIZE)
        b = a.copy()
        c = a.copy()
        b[0x111] = 1  # naturally changing byte excluded
        c[0x111] = 2
        a[0x1234] = b[0x1234] = 7
        c[0x1234] = 8
        report = d.analyze(a, b, c, "coin_up")
        rows = report["suggested_candidates"]
        self.assertTrue(any(x["logical_ram_offset_hex"] == "0x001234" and
                            x["width_bytes"] == 1 for x in rows))
        self.assertFalse(any(x["logical_ram_offset_hex"] == "0x000111" for x in rows))
        self.assertGreater(report["bytes_changed_during_control"], 0)

    def test_star_expected_delta(self):
        a = bytearray(d.SIZE)
        b = a.copy()
        c = a.copy()
        a[0x234] = b[0x234] = 149
        c[0x234] = 150
        self.assertTrue(any(x["logical_ram_offset_hex"] == "0x000234"
                            for x in d.analyze(a, b, c, "star_up")["suggested_candidates"]))

    def test_lives_research_offset_ranked(self):
        a = bytearray(d.SIZE)
        b = a.copy()
        c = a.copy()
        a[0x09F2F4] = b[0x09F2F4] = 5
        c[0x09F2F4] = 4
        r = d.analyze(a, b, c, "life_down")
        self.assertEqual(r["suggested_candidates"][0]["eu_literature_hint"], "lives")
        self.assertEqual(r["suggested_candidates"][0]["physical_arm9_address_hex"], "0x0209F2F4")

    def test_health_down_detected(self):
        a = bytearray(d.SIZE)
        b = a.copy()
        c = a.copy()
        a[0x11117C] = b[0x11117C] = 8
        c[0x11117C] = 6
        r = d.analyze(a, b, c, "health_down")
        self.assertTrue(any(x["eu_literature_hint"] == "health_candidate_a"
                            for x in r["suggested_candidates"]))

    def test_control_removes_false_event(self):
        a = bytearray(d.SIZE)
        b = a.copy()
        c = a.copy()
        a[0x100] = 4
        b[0x100] = 5
        c[0x100] = 6
        r = d.analyze(a, b, c, "coin_up")
        self.assertEqual(r["total_candidates"], 0)

    def test_wrong_byte_lengths_block(self):
        with self.assertRaisesRegex(d.CaptureError, "size"):
            d.analyze(b"12", b"12", b"12", "coin_up")

    def test_unknown_event_blocks(self):
        with self.assertRaisesRegex(d.CaptureError, "Unknown"):
            d.analyze(bytearray(d.SIZE), bytearray(d.SIZE), bytearray(d.SIZE), "unofficial")

    def test_realistic_synthetic_fixture_and_sanitized_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "frames"
            s.generate(folder)
            captures = paths(folder)
            with self.assertRaisesRegex(d.CaptureError, "unverified"):
                d.summary(captures, "coin_up", 80, allow_unverified=False)
            report = d.summary(captures, "coin_up", 80, allow_unverified=True)
            self.assertFalse(report["dsi_physical_tested"])
            self.assertFalse(report["rom_ra_hash_verified_by_analyzer"])
            self.assertFalse(report["official_unlocks_sent"])
            self.assertFalse(report["official_ra_conditions_used"])
            self.assertEqual(report["game_header_seen_by_bizhawk"], "UNVERIFIED")
            self.assertEqual(report["first_frame"], 100)
            self.assertEqual(report["event_frame"], 145)
            self.assertTrue(any(x["logical_ram_offset_hex"] == "0x022220"
                                for x in report["suggested_candidates"]))
            self.assertFalse(any(x["logical_ram_offset_hex"] == "0x044440"
                                 for x in report["suggested_candidates"]))

    def test_refuse_wrong_header_and_non_atomic_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "frames"
            s.generate(folder)
            captures = paths(folder)
            meta_path = captures[0].with_suffix(".json")
            meta = json.loads(meta_path.read_text())
            meta["game_code"] = "ASME"
            meta_path.write_text(json.dumps(meta))
            with self.assertRaisesRegex(d.CaptureError, "Wrong game"):
                d.summary(captures, "coin_up", 20, True)
            meta["game_code"] = "UNVERIFIED"
            meta["frame_after"] = meta["frame_before"] + 3
            meta_path.write_text(json.dumps(meta))
            with self.assertRaisesRegex(d.CaptureError, "not atomic"):
                d.summary(captures, "coin_up", 20, True)

    def test_refuse_cross_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "frames"
            s.generate(folder)
            old = paths(folder)
            renamed = folder / "UNRELATED_after.bin"
            renamed.write_bytes(old[2].read_bytes())
            renamed.with_suffix(".json").write_bytes(old[2].with_suffix(".json").read_bytes())
            with self.assertRaisesRegex(d.CaptureError, "same labeled session"):
                d.summary((old[0], old[1], renamed), "coin_up", 20, True)

    def test_refuse_wrong_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "frames"
            s.generate(folder)
            captures = paths(folder)
            meta_path = captures[1].with_suffix(".json")
            meta = json.loads(meta_path.read_text())
            meta["frame_before"] = 90
            meta["frame_after"] = 90
            meta_path.write_text(json.dumps(meta))
            with self.assertRaisesRegex(d.CaptureError, "not strictly increasing"):
                d.summary(captures, "coin_up", 20, True)

    def test_sanitized_cli_output_no_ram_dump(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "frames"
            s.generate(folder)
            p = paths(folder)
            output = Path(tmp) / "report.json"
            argv = sys.argv
            buff = io.StringIO()
            try:
                sys.argv = ["script","--before",str(p[0]),"--idle",str(p[1]),
                            "--after",str(p[2]),"--event","coin_up","--out",str(output),
                            "--allow-unverified-header"]
                with contextlib.redirect_stdout(buff):
                    d.main()
            finally:
                sys.argv = argv
            record = json.loads(output.read_text())
            self.assertEqual(record["format"], "DSIRB048_RAM_DIFF_SANITIZED_V1")
            self.assertNotIn("memory_dump", record)
            self.assertNotIn("private_memory", buff.getvalue())
            self.assertGreater(record["total_candidates"], 0)

    def test_output_overwrite_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "frames"
            s.generate(folder)
            p = paths(folder)
            output = Path(tmp) / "report.json"
            output.write_text("EXISTS", encoding="utf-8")
            oldargv = sys.argv
            try:
                sys.argv = ["script", "--before", str(p[0]), "--idle", str(p[1]),
                            "--after", str(p[2]), "--event", "coin_up",
                            "--out", str(output), "--allow-unverified-header"]
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    d.main()
            finally:
                sys.argv = oldargv
            self.assertEqual(output.read_text(), "EXISTS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
