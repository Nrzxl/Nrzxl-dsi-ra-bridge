import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "dsi"

class ARM7Isolation034G(unittest.TestCase):
    def read(self, stage):
        base = ROOT / ("probe-034g-" + stage)
        return ((base/"source/main.c").read_text(),
                (base/"arm7/source/main.c").read_text(),
                (base/"arm7/Makefile").read_text(),
                (base/"Makefile").read_text())

    def test_same_arm9_with_no_rom_or_network(self):
        for stage, label in [("core","CORE"),("fifo","FIFO"),("update","UPDATE")]:
            arm9,arm7,arm7mk,mk=self.read(stage)
            self.assertIn("DSIRB 034G " + label + " TEST",arm9)
            self.assertIn("MAIN REACHED: YES",arm9)
            self.assertIn("ARM7ELF",mk)
            self.assertIn("SPDX-License-Identifier: Zlib",arm7)
            for forbidden in ("fatInitDefault(", "fopen(", "mkdir(", "chainload(",
                              "session_login(", "session_start(", "Wifi_ConnectAP("):
                self.assertNotIn(forbidden,arm9 + arm7)

    def test_wifi_only_progresses_incrementally(self):
        _,core,core_mk,_=self.read("core")
        _,fifo,fifo_mk,_=self.read("fifo")
        _,update,update_mk,_=self.read("update")
        self.assertNotIn("dswifi7.h",core)
        self.assertNotIn("installWifiFIFO()",core)
        self.assertNotIn("Wifi_Update()",core)
        self.assertNotIn("-ldswifi7",core_mk)
        self.assertIn("installWifiFIFO()",fifo)
        self.assertNotIn("Wifi_Update()",fifo)
        self.assertIn("-ldswifi7",fifo_mk)
        self.assertIn("installWifiFIFO()",update)
        self.assertIn("Wifi_Update()",update)
        self.assertIn("-ldswifi7",update_mk)
        self.assertNotIn("freeze_wifi",core+fifo+update)

if __name__ == "__main__":
    unittest.main(verbosity=2)
