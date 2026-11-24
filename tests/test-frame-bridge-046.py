"""0.4.6 host bridge: deterministic synthetic-only fail-closed tests."""
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("frame_bridge_046", ROOT / "scripts/frame-bridge-046.py")
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)


class Bridge046(unittest.TestCase):
    def setUp(self):
        self.frames = list(bridge.synthetic_frames())
        self.packets = [bridge.encode(f) for f in self.frames]

    def test_roundtrip_all_frames_and_regions(self):
        for orig, packet in zip(self.frames, self.packets):
            self.assertEqual(bridge.decode(packet), orig)

    def test_fixed_size_overhead_and_body_budget(self):
        packet = self.packets[0]
        self.assertEqual(len(packet), bridge.BASE.size + 4 + 2 * bridge.REGION.size + 3)
        self.assertLessEqual(len(packet), 1200)

    def test_crc32_single_bit_corruption_halts(self):
        receiver = bridge.Receiver()
        bad = bytearray(self.packets[0])
        bad[-1] ^= 0x01
        with self.assertRaisesRegex(bridge.FrameError, "CRC32"):
            receiver.receive(bytes(bad))
        self.assertTrue(receiver.halted)
        with self.assertRaisesRegex(bridge.FrameError, "halted"):
            receiver.receive(self.packets[0])

    def test_sequence_gap_halts_instead_of_skipping_frame(self):
        receiver = bridge.Receiver()
        receiver.receive(self.packets[0])
        with self.assertRaisesRegex(bridge.FrameError, "Sequence gap"):
            receiver.receive(self.packets[2])
        self.assertTrue(receiver.halted)

    def test_duplicate_packet_halts(self):
        receiver = bridge.Receiver()
        receiver.receive(self.packets[0])
        with self.assertRaisesRegex(bridge.FrameError, "Sequence gap"):
            receiver.receive(self.packets[0])

    def test_missing_frame_even_if_sequence_is_contiguous(self):
        first, second = self.frames[0], self.frames[1]
        changed = bridge.Frame(second.session, second.game_hash, 1, 42, second.regions)
        receiver = bridge.Receiver()
        receiver.receive(bridge.encode(first))
        with self.assertRaisesRegex(bridge.FrameError, "Missing/duplicate frame"):
            receiver.receive(bridge.encode(changed))

    def test_identity_switch_halts(self):
        first, second = self.frames[0], self.frames[1]
        switched = bridge.Frame(bytes.fromhex("1234" * 8), second.game_hash, 1, 1, second.regions)
        receiver = bridge.Receiver()
        receiver.receive(bridge.encode(first))
        with self.assertRaisesRegex(bridge.FrameError, "session switch"):
            receiver.receive(bridge.encode(switched))

    def test_hash_and_version_mismatch_rejected(self):
        first = self.frames[0]
        with self.assertRaisesRegex(bridge.FrameError, "Game hash"):
            bridge.encode(bridge.Frame(first.session, bytes(16), 0, 0, first.regions))
        packet = bytearray(self.packets[0])
        packet[4] += 1
        with self.assertRaisesRegex(bridge.FrameError, "version"):
            bridge.decode(bytes(packet))

    def test_sparse_memory_must_come_from_current_frame(self):
        receiver = bridge.Receiver()
        receiver.receive(self.packets[0])
        self.assertEqual(receiver.read(0x100, 2), b"\0\0")
        self.assertEqual(receiver.read(bridge.DTCM_BASE + 0x20, 1), b"\0")
        with self.assertRaisesRegex(bridge.FrameError, "Unavailable"):
            receiver.read(0x200, 1)
        with self.assertRaisesRegex(bridge.FrameError, "outside"):
            receiver.read(0x400000, 1)
        receiver.receive(self.packets[1])
        self.assertEqual(receiver.read(0x100, 2), b"\0\1")

    def test_truncated_region_and_payload(self):
        with self.assertRaisesRegex(bridge.FrameError, "length|size"):
            bridge.decode(self.packets[0][:-1])
        first = self.frames[0]
        broken = bridge.Frame(first.session, first.game_hash, 0, 0, (bridge.Region(0, 0x400000, b"1"),))
        with self.assertRaisesRegex(bridge.FrameError, "outside"):
            bridge.encode(broken)

    def test_overlapping_or_unsorted_regions_fail(self):
        f = self.frames[0]
        for reg in (
            (bridge.Region(0, 10, b"abc"), bridge.Region(0, 12, b"123")),
            (bridge.Region(1, 0, b"a"), bridge.Region(0, 1, b"b")),
        ):
            with self.assertRaisesRegex(bridge.FrameError, "sorted"):
                bridge.encode(bridge.Frame(f.session, f.game_hash, 0, 0, reg))

    def test_max_body_and_region_count_limits(self):
        f = self.frames[0]
        oversized = tuple(bridge.Region(0, i * 256, b"a" * 256) for i in range(5))
        with self.assertRaisesRegex(bridge.FrameError, "budget"):
            bridge.encode(bridge.Frame(f.session, f.game_hash, 0, 0, oversized))
        too_many = tuple(bridge.Region(0, i * 2, b"a") for i in range(33))
        with self.assertRaisesRegex(bridge.FrameError, "count"):
            bridge.encode(bridge.Frame(f.session, f.game_hash, 0, 0, too_many))

    def test_stream_framing_roundtrip_and_truncation_fail(self):
        stream = bridge.dump_stream(self.frames)
        decoded, receiver = bridge.load_stream(stream)
        self.assertEqual(decoded, self.frames)
        self.assertEqual(receiver.accepted, 5)
        with self.assertRaisesRegex(bridge.FrameError, "Bad framed packet size"):
            bridge.load_stream(stream[:-1])
        with self.assertRaisesRegex(bridge.FrameError, "Empty"):
            bridge.load_stream(b"")

    def test_demo_report_no_real_awards(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "demo"
            orig_argv = sys.argv
            try:
                sys.argv = ["script", "demo", "--out", str(dest)]
                bridge.main()
            finally:
                sys.argv = orig_argv
            report = json.loads((dest / "synthetic-report-046.json").read_text())
            self.assertEqual(report["accepted_frames"], 5)
            self.assertFalse(report["capture_on_dsi"])
            self.assertFalse(report["official_unlocks_sent"])
            self.assertFalse(report["official_achievement_definitions_used"])
            self.assertEqual(len((dest / "synthetic-trace-046.csv").read_text().splitlines()), 6)

    def test_counter_wrap_and_session_all_zero_fail(self):
        f = self.frames[0]
        for bad_seq, bad_frame in ((0xffffffff, 0), (0, 0xffffffff)):
            r = bridge.Receiver()
            with self.assertRaisesRegex(bridge.FrameError, "gap|wrap"):
                r.receive(bridge.encode(bridge.Frame(f.session, f.game_hash, bad_seq, bad_frame, f.regions)))
        with self.assertRaisesRegex(bridge.FrameError, "nonzero"):
            bridge.encode(bridge.Frame(bytes(16), f.game_hash, 0, 0, f.regions))

    def test_hard_limit_for_unknown_bank(self):
        f = self.frames[0]
        with self.assertRaisesRegex(bridge.FrameError, "Unsupported"):
            bridge.encode(bridge.Frame(f.session, f.game_hash, 0, 0, (bridge.Region(2, 0, b"x"),)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
