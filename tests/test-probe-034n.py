"""034N fail-closed gates: ARM7 stages vs selective Wifi_Update symbol link."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/"dsi"
C=ROOT/"probe-034n-core"
W=ROOT/"probe-034n-update-link"

class ARM7Stages034N(unittest.TestCase):
    def test_identical_arm9(self):
        a=(C/"source/main.c").read_bytes()
        self.assertEqual(a,(W/"source/main.c").read_bytes())
        for expected in (b"MAIN REACHED: YES",b"STAGE 1:",b"STAGE 2:",
                         b"LOOP ALIVE:",b"FIFO_USER_03",b"KEY_START"):
            self.assertIn(expected,a)

    def test_arm7_stages_and_delta(self):
        a=(C/"arm7/source/main.c").read_text()
        b=(W/"arm7/source/main.c").read_text()
        for s in (a,b):
            self.assertIn("fifoSendValue32(FIFO_USER_03, 0x4E370001u)",s)
            self.assertIn("fifoSendValue32(FIFO_USER_03, 0x4E370002u)",s)
            self.assertLess(s.index("fifoInit();"),s.index("0x4E370001u"))
            self.assertLess(s.index("irqEnable(IRQ_VBLANK);"),s.index("0x4E370002u"))
            self.assertIn("SPDX-License-Identifier: Zlib",s)
        self.assertNotIn("#include <dswifi7.h>",a)
        self.assertIn("#include <dswifi7.h>",b)
        self.assertIn("= Wifi_Update;",b)
        self.assertNotIn("Wifi_Update();",b) # function linked but never called
        self.assertNotIn("installWifiFIFO();",b)
        self.assertNotIn("Wifi_Init(",b)

    def test_no_fat_network_or_nand(self):
        for p in (C,W):
            m=(p/"Makefile").read_text()
            am=(p/"arm7/Makefile").read_text()
            self.assertIn("rom_arm9/Makefile",m)
            self.assertIn("rom_arm9arm7/Makefile.arm7",am)
            self.assertIn("-lnds7",am)
            source=(p/"source/main.c").read_text()
            arm=(p/"arm7/source/main.c").read_text()
            for forbidden in ("Wifi_InitDefault(", "Wifi_AutoConnect(", "Wifi_ConnectAP(",
                              "fatInitDefault(", "fopen(", "fwrite(", "mkdir(",
                              "socket(", "connect(", "nds-bootstrap", "chainload(",
                              "session_login(", "rcheevos", "REG_SCFG", "REG_MBK",
                              "swiSoftReset("):
                self.assertNotIn(forbidden,source+arm)

    def test_link_only_one_archive_symbol(self):
        core=(C/"arm7/Makefile").read_text()
        link=(W/"arm7/Makefile").read_text()
        self.assertNotIn("-ldswifi7",core)
        self.assertIn("-ldswifi7 -lnds7",link)
        self.assertIn("$(BLOCKSDS)/libs/dswifi",link)

if __name__=="__main__":
    unittest.main(verbosity=2)
