import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIR = ROOT / "dsi"

class Probe034FSafety(unittest.TestCase):
    def test_three_variants_and_no_game_or_write(self):
        for p, label in [("f1-ui","UI"),("f2-arm7","ARM7"),("f3-fat","FAT")]:
            folder = DIR / ("probe-034f-" + p)
            source = (folder/"source/main.c").read_text()
            mk = (folder/"Makefile").read_text()
            self.assertIn("MAIN REACHED: YES", source)
            self.assertIn("DSIRB 034F " + label, source)
            self.assertIn("DScheevos-style dual UI", source)
            self.assertNotIn("boot_game(", source)
            self.assertNotIn("chainload(", source)
            self.assertNotIn("session_start(", source)
            self.assertNotIn("session_login(", source)
            self.assertNotIn('fopen(', source)
            self.assertNotIn('mkdir(', source)
            self.assertIn('rom_arm9/Makefile', mk)

    def test_custom_arm7_progression(self):
        for p in ("f2-arm7","f3-fat"):
            folder = DIR / ("probe-034f-" + p)
            mk = (folder/"Makefile").read_text()
            arm7 = (folder/"arm7/source/main.c").read_text()
            self.assertIn("ARM7ELF", mk)
            self.assertIn("dswifi7.h", arm7)
            self.assertIn("SPDX-License-Identifier: Zlib", arm7)
        self.assertFalse((DIR/"probe-034f-f1-ui/arm7").exists())

    def test_fat_is_manual_and_last(self):
        for p in ("f1-ui","f2-arm7"):
            self.assertNotIn("fatInitDefault", (DIR/("probe-034f-"+p)/"source/main.c").read_text())
        data = (DIR/"probe-034f-f3-fat/source/main.c").read_text()
        self.assertIn("fatInitDefault", data)
        self.assertIn("keys & KEY_A", data)
        self.assertLess(data.index("keys & KEY_A"), data.index("fatInitDefault()"))
        self.assertIn("FAT MOUNT: attempting...", data)

if __name__ == "__main__":
    unittest.main(verbosity=2)
