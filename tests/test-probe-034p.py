"""034P: physical O2 regression baseline, add one DSWiFi symbol at a time.

These safety gates are compile-time only; no actual DSi boot, Wi-Fi, game
or RetroAchievements is inferred from running them.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
O2=ROOT/"dsi"/"probe-034o-receive"
P0=ROOT/"dsi"/"probe-034p-control"
P1=ROOT/"dsi"/"probe-034p-update-link"
P2=ROOT/"dsi"/"probe-034p-fifo-link"

def src(p,part):return (p/part).read_text()
class SymbolLink034P(unittest.TestCase):
    def test_arm9_source_and_verified_o2_baseline(self):
        original=src(O2,"source/main.c")
        self.assertIn("STAGE 1: %-7s",original)
        self.assertIn("STAGE 2: %-7s",original)
        self.assertIn("MAIN REACHED: YES",original)
        self.assertIn("LOOP ALIVE:",original)
        self.assertIn("fifoCheckValue32(FIFO_USER_03)",original)
        self.assertIn("fifoGetValue32(FIFO_USER_03)",original)
        for p in (P0,P1,P2):
            self.assertEqual(original,src(p,"source/main.c"),
               "No ARM9 source changes are permitted from physical O2 PASS")
        self.assertEqual(src(O2,"arm7/source/main.c"),src(P0,"arm7/source/main.c"))
        self.assertEqual(src(O2,"arm7/Makefile"),src(P0,"arm7/Makefile"))

    def test_only_one_new_symbol_per_arm7_variant(self):
        a=src(P0,"arm7/source/main.c")
        b=src(P1,"arm7/source/main.c")
        c=src(P2,"arm7/source/main.c")
        addition=[
          "/* Link-only probe: pointer retained, Wi-Fi functions are NOT called. */",
          "#include <dswifi7.h>",
          "static void (*volatile dsirb_wifi_update_symbol)(void) = Wifi_Update;",
          ""
        ]
        inj=[
          "    /* Force symbol inclusion without executing network functions. */",
          '    __asm__ volatile ("" : : "r"(dsirb_wifi_update_symbol) : "memory");',
          ""
        ]
        self.assertEqual(b.replace("\n".join(addition),"").replace("\n".join(inj),""),a)
        cadd="static void (*volatile dsirb_wifi_fifo_symbol)(void) = installWifiFIFO;\n"
        cinj='    __asm__ volatile ("" : : "r"(dsirb_wifi_fifo_symbol) : "memory");\n'
        self.assertEqual(c.replace(cadd,"").replace(cinj,""),b)
        self.assertNotIn("Wifi_Update();",b)
        self.assertNotIn("installWifiFIFO();",c)
        self.assertNotIn("Wifi_Init(",c)

    def test_only_needed_libraries(self):
        mk0=src(P0,"arm7/Makefile")
        mk1=src(P1,"arm7/Makefile")
        mk2=src(P2,"arm7/Makefile")
        self.assertNotIn("-ldswifi7",mk0)
        for m in (mk1,mk2):
            self.assertIn("LIBS       := -ldswifi7 -lnds7",m)
            self.assertIn("$(BLOCKSDS)/libs/dswifi",m)
        self.assertEqual(mk1,mk2)
        for p in (P0,P1,P2):
            self.assertIn("rom_arm9/Makefile",src(p,"Makefile"))
            self.assertIn("SPDX-License-Identifier: Zlib",src(p,"arm7/source/main.c"))
            self.assertEqual(src(p,"arm7/source/main.c").count("fifoSendValue32(FIFO_USER_03"),2)

    def test_no_actual_network_rom_sd_or_firmware_access(self):
        banned=(
            "Wifi_InitDefault(", "Wifi_Init(", "Wifi_Update();",
            "installWifiFIFO();", "Wifi_AutoConnect(", "Wifi_ConnectAP(",
            "fatInitDefault(", "fopen(", "fwrite(", "mkdir(", "socket(",
            "connect(", "nds-bootstrap", "chainload(", "session_login(",
            "rcheevos", "REG_SCFG", "REG_MBK", "swiSoftReset(",
            "systemReboot("
        )
        for p in (P0,P1,P2):
            code=src(p,"source/main.c")+"\n"+src(p,"arm7/source/main.c")
            for token in banned:
                self.assertNotIn(token,code)
        self.assertNotIn("#include <dswifi7.h>",src(P0,"arm7/source/main.c"))
        self.assertNotIn("dsirb_wifi_update_symbol",src(P0,"arm7/source/main.c"))

if __name__=="__main__":unittest.main(verbosity=2)
