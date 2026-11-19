"""034L safety gates for inert NWRAM padding physical test."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/"dsi"
C=ROOT/"probe-034l-control"
P=ROOT/"probe-034l-pad"

class NWRAM034L(unittest.TestCase):
    def test_arm9_identical(self):
        code=(C/"source/main.c").read_bytes()
        self.assertEqual(code,(P/"source/main.c").read_bytes())
        self.assertIn(b"MAIN REACHED: YES",code)
        self.assertIn(b"LOOP ALIVE:",code)
        self.assertIn(b"KEY_START",code)

    def test_arm7_padding_is_only_change(self):
        c=(C/"arm7/source/main.c").read_text()
        p=(P/"arm7/source/main.c").read_text()
        self.assertIn("dsirb_twl_bytes[17848]",p)
        self.assertIn("dsirb_twl_bss[13300]",p)
        self.assertIn('section(".twl")',p)
        self.assertIn('section(".twl_bss")',p)
        self.assertNotIn("dsirb_twl_bytes",c)
        self.assertNotIn("dsirb_twl_bss",c)
        self.assertIn('"" : : "r"',p)
        self.assertEqual((C/"arm7/Makefile").read_bytes(),(P/"arm7/Makefile").read_bytes())
        self.assertIn("SPDX-License-Identifier: Zlib",p)

    def test_no_wifi_network_sd_or_retail(self):
        for path in (C,P):
            text="\n".join(f.read_text() for f in (path/"source/main.c",
                path/"arm7/source/main.c",path/"Makefile",path/"arm7/Makefile"))
            for word in ("#include <dswifi","-ldswifi","installWifiFIFO(",
                         "Wifi_Update(","Wifi_InitDefault(","Wifi_AutoConnect(",
                         "Wifi_ConnectAP(","fatInitDefault(","fopen(","fwrite(",
                         "mkdir(","session_login(","rcheevos","boot_game(",
                         "chainload(","nds-bootstrap","REG_SCFG","REG_MBK",
                         "swiSoftReset("):
                self.assertNotIn(word,text)

if __name__=="__main__":unittest.main(verbosity=2)
