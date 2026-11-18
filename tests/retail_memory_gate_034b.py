"""Read-only 034-B gate tested with synthetic images ONLY; no retail ROMs."""
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import retail_memory_gate_034b as memory_gate
spec = importlib.util.spec_from_file_location("baseline_fixture_034",
                                              ROOT / "tests/retail_preflight_034.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def with_table(data, offset=0x2100, address=0x02300000, size=0x1000,
               bss=0x200, header_arm=0x50, reversed_init=False):
    struct.pack_into("<I", data, header_arm, offset)
    struct.pack_into("<I", data, header_arm + 4, 32)
    struct.pack_into("<8I", data, offset, 7, address, size, bss,
                     20 if reversed_init else 8, 8 if reversed_init else 20, 3, 0)
    struct.pack_into("<H", data, 0x15E, fixtures.preflight.crc16(data[:0x15E]))
    return data


class ReadOnlyGateTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "SYNTHETIC_ONLY.nds"

    def save(self, data):
        self.path.write_bytes(data)
        return self.path

    def test_ntr_no_declared_overlap_is_not_ready(self):
        original = fixtures.synthetic()
        result = memory_gate.inspect(self.save(original))
        self.assertEqual(result["status"], "NO_DECLARED_OVERLAP_RUNTIME_UNPROVEN")
        self.assertFalse(result["retail_monitor_ready"])
        self.assertFalse(result["safe_to_patch"])
        self.assertEqual(result["declared_overlay_entries"], 0)
        self.assertEqual(self.path.read_bytes(), original)

    def test_twl_sections_never_assumed_safe(self):
        result = memory_gate.inspect(self.save(fixtures.synthetic(2)))
        self.assertEqual(result["unit_code"], 2)
        self.assertFalse(result["retail_monitor_ready"])

    def test_nonoverlapping_arm9_overlay(self):
        data = with_table(fixtures.synthetic())
        result = memory_gate.inspect(self.save(data))
        self.assertEqual(result["declared_overlay_entries"], 1)
        self.assertEqual(result["declared_overlaps"], [])

    def test_declared_overlay_reservation_collision(self):
        data = with_table(fixtures.synthetic(), address=0x02D90000)
        result = memory_gate.inspect(self.save(data))
        self.assertEqual(result["status"], "BLOCKED_DECLARED_RESERVATION_OVERLAP")
        self.assertTrue(result["declared_overlaps"])
        self.assertFalse(result["safe_to_patch"])

    def test_declared_arm9_collision(self):
        data = fixtures.synthetic()
        struct.pack_into("<I", data, 0x24, 0x02D80000)
        struct.pack_into("<I", data, 0x28, 0x02D80000)
        struct.pack_into("<H", data, 0x15E, fixtures.preflight.crc16(data[:0x15E]))
        result = memory_gate.inspect(self.save(data))
        self.assertEqual(result["status"], "BLOCKED_DECLARED_RESERVATION_OVERLAP")

    def test_overlay_bad_table_bounds(self):
        data = fixtures.synthetic()
        struct.pack_into("<I", data, 0x50, 0x2FF0)
        struct.pack_into("<I", data, 0x54, 0x40)
        struct.pack_into("<H", data, 0x15E, fixtures.preflight.crc16(data[:0x15E]))
        with self.assertRaisesRegex(ValueError, "truncated"):
            memory_gate.inspect(self.save(data))

    def test_overlay_reversed_static_range(self):
        with self.assertRaisesRegex(ValueError, "reversed"):
            memory_gate.inspect(self.save(with_table(fixtures.synthetic(), reversed_init=True)))

    def test_overlay_size_outside_ram_bounds(self):
        with self.assertRaisesRegex(ValueError, "footprint"):
            memory_gate.inspect(self.save(with_table(fixtures.synthetic(),
                                                     address=0x03FFFFF0, size=0x200)))

    def test_incomplete_table_rejected(self):
        data = fixtures.synthetic()
        struct.pack_into("<I", data, 0x50, 0x2100)
        struct.pack_into("<H", data, 0x15E, fixtures.preflight.crc16(data[:0x15E]))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            memory_gate.inspect(self.save(data))

    def test_cli_reads_without_mutation(self):
        data = with_table(fixtures.synthetic())
        self.save(data)
        result = subprocess.run([sys.executable, str(SCRIPTS/"retail_memory_gate_034b.py"),
                                 str(self.path)], capture_output=True, text=True, check=True)
        self.assertFalse(json.loads(result.stdout)["retail_monitor_ready"])
        self.assertNotIn(str(self.path), result.stdout)
        self.assertEqual(self.path.read_bytes(), data)

    def test_cli_conflict_exits_nonzero(self):
        data = with_table(fixtures.synthetic(), address=0x02D90000)
        self.save(data)
        result = subprocess.run([sys.executable, str(SCRIPTS/"retail_memory_gate_034b.py"),
                                 str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["status"],
                         "BLOCKED_DECLARED_RESERVATION_OVERLAP")
        self.assertEqual(self.path.read_bytes(), data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
