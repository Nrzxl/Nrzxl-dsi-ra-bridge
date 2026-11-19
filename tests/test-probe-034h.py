import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "dsi"

def contents(stage):
    folder = ROOT / ("probe-034h-" + stage)
    return {
      "arm7": (folder / "arm7/source/main.c").read_text(),
      "arm9": (folder / "source/main.c").read_text(),
      "mk": (folder / "arm7/Makefile").read_text(),
      "main_mk": (folder / "Makefile").read_text(),
    }

class Wifi034HSafety(unittest.TestCase):
    def test_link_only_never_calls_wifi(self):
        v = contents("link")
        self.assertIn("MAIN REACHED: YES", v["arm9"])
        self.assertIn("= installWifiFIFO", v["arm7"])
        self.assertNotIn("    installWifiFIFO();", v["arm7"])
        self.assertIn("-ldswifi7", v["mk"])
        self.assertIn("SPDX-License-Identifier: Zlib", v["arm7"])

    def test_manual_gate_before_wifi(self):
        v = contents("gate")
        self.assertIn("MAIN REACHED: YES", v["arm9"])
        self.assertIn("fifoSendValue32(FIFO_USER_02", v["arm9"])
        self.assertIn("if (keys & KEY_A) break;", v["arm9"])
        self.assertLess(v["arm9"].index("MAIN REACHED: YES"),
                        v["arm9"].index("fifoSendValue32(FIFO_USER_02"))
        self.assertIn("if (arm9_requested_wifi_init", v["arm7"])
        self.assertIn("    installWifiFIFO();", v["arm7"])
        self.assertIn("fifoSendValue32(FIFO_USER_02", v["arm7"])

    def test_no_rom_fat_or_achievements(self):
        for variant in ("link", "gate"):
            v = contents(variant)
            combined = v["arm9"] + v["arm7"]
            for forbidden in ("fatInitDefault(", "fopen(", "fwrite(", "mkdir(",
                              "chainload(", "session_login(", "session_start(",
                              "Wifi_ConnectAP(", "Wifi_AutoConnect(", "swiSoftReset("):
                self.assertNotIn(forbidden, combined)

if __name__ == "__main__":
    unittest.main(verbosity=2)
