"""Offline tests. All .nds files generated here are synthetic, never retail ROMs."""
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/retail_preflight_034.py'
spec = importlib.util.spec_from_file_location('preflight_034', SOURCE)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def synthetic(unit=0):
    raw = bytearray(0x3000)
    raw[:9] = b'TEST ONLY'
    raw[0x12] = unit
    hdr = 0x1000 if unit else 0x200
    struct.pack_into('<I', raw, 0x84, hdr)
    struct.pack_into('<4I', raw, 0x20, 0x1000, 0x02000000, 0x02000000, 0x100)
    struct.pack_into('<4I', raw, 0x30, 0x1100, 0x037F8000, 0x037F8000, 0x100)
    struct.pack_into('<I', raw, 0x80, 0x2400)
    struct.pack_into('<I', raw, 0x68, 0x1800)
    if unit:
        struct.pack_into('<4I', raw, 0x1C0, 0x1200, 0x02300000, 0x02300000, 0x80)
        struct.pack_into('<4I', raw, 0x1D0, 0x1280, 0x02301000, 0x02301000, 0x80)
    struct.pack_into('<H', raw, 0x15E, preflight.crc16(raw[:0x15E]))
    return raw


class Preflight(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'synthetic.nds'

    def save(self, image):
        self.path.write_bytes(image)
        return self.path

    def test_ntr_valid_never_monitor_ready_and_unchanged(self):
        image = synthetic()
        path = self.save(image)
        result = preflight.inspect_rom(path)
        self.assertEqual(result['status'], 'STRUCTURE_PASS_RETAIL_MONITOR_NOT_PROVEN')
        self.assertFalse(result['retail_monitor_ready'])
        self.assertEqual(len(result['segments']), 2)
        self.assertEqual(path.read_bytes(), image)

    def test_twl_has_additional_segments(self):
        result = preflight.inspect_rom(self.save(synthetic(2)))
        self.assertEqual(len(result['segments']), 4)
        self.assertEqual(result['mode'], 'TWL-capable')

    def test_invalid_crc_rejected(self):
        raw = synthetic()
        raw[1] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC16'):
            preflight.inspect_rom(self.save(raw))

    def test_truncated_arm9_rejected(self):
        raw = synthetic()
        struct.pack_into('<I', raw, 0x20, len(raw) - 0x40)
        struct.pack_into('<H', raw, 0x15E, preflight.crc16(raw[:0x15E]))
        with self.assertRaisesRegex(ValueError, 'truncated'):
            preflight.inspect_rom(self.save(raw))

    def test_overlapping_segments_rejected(self):
        raw = synthetic()
        struct.pack_into('<I', raw, 0x30, 0x1080)
        struct.pack_into('<H', raw, 0x15E, preflight.crc16(raw[:0x15E]))
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            preflight.inspect_rom(self.save(raw))

    def test_entry_outside_segment_rejected(self):
        raw = synthetic()
        struct.pack_into('<I', raw, 0x24, 0x02500000)
        struct.pack_into('<H', raw, 0x15E, preflight.crc16(raw[:0x15E]))
        with self.assertRaisesRegex(ValueError, 'entry'):
            preflight.inspect_rom(self.save(raw))

    def test_unknown_unit_rejected(self):
        raw = synthetic()
        raw[0x12] = 1
        struct.pack_into('<H', raw, 0x15E, preflight.crc16(raw[:0x15E]))
        with self.assertRaisesRegex(ValueError, 'unit code'):
            preflight.inspect_rom(self.save(raw))

    def test_cli_failure_reports_blocked_and_does_not_mutate(self):
        raw = synthetic()
        raw[0] ^= 1
        path = self.save(raw)
        before = path.read_bytes()
        call = subprocess.run([sys.executable, str(SOURCE), str(path)],
                              capture_output=True, text=True)
        self.assertEqual(call.returncode, 2)
        self.assertEqual(json.loads(call.stdout)['status'], 'BLOCKED')
        self.assertEqual(path.read_bytes(), before)

    def test_cli_success_explicitly_not_ready(self):
        path = self.save(synthetic())
        call = subprocess.run([sys.executable, str(SOURCE), str(path)],
                              capture_output=True, text=True, check=True)
        doc = json.loads(call.stdout)
        self.assertFalse(doc['retail_monitor_ready'])
        self.assertEqual(doc['official_awards'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
