"""Source and architecture safety gates for the official BlocksDS ARM7 A/B."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1] / "dsi"
A=ROOT / "probe-034j-official-base"
B=ROOT / "probe-034j-official-wifi"

class Official034J(unittest.TestCase):
    def test_same_arm9_c_source(self):
        a=(A/"source/main.c").read_bytes()
        b=(B/"source/main.c").read_bytes()
        self.assertEqual(a,b,"Control and WiFi test MUST have identical ARM9 C source")
        s=a.decode()
        self.assertIn("MAIN REACHED: YES",s)
        self.assertIn("LOOP ALIVE:",s)
        self.assertIn("keysDown() & KEY_START",s)
        for forbidden in ("fatInitDefault(", "fatMount", "fopen(", "fwrite(", "remove(",
                          "Wifi_InitDefault(", "Wifi_ConnectAP(", "Wifi_AutoConnect(",
                          "installWifiFIFO(", "Wifi_Update(", "socket(", "connect(",
                          "chainload(", "session_login(", "rcheevos", "nds-bootstrap",
                          "DC_FlushRange(", "REG_SCFG", "swiSoftReset("):
            self.assertNotIn(forbidden,s)

    def test_prebuilt_arm7_and_no_custom_arm7(self):
        am=(A/"Makefile").read_text()
        bm=(B/"Makefile").read_text()
        self.assertIn("ARM7ELF       := $(BLOCKSDS)/sys/arm7/main_core/arm7_maxmod.elf",am)
        self.assertIn("ARM7ELF       := $(BLOCKSDS)/sys/arm7/main_core/arm7_dswifi_maxmod.elf",bm)
        self.assertIn("rom_arm9/Makefile",am)
        self.assertIn("rom_arm9/Makefile",bm)
        self.assertIn("LIBS          := -lnds9",am)
        self.assertIn("LIBS          := -lnds9",bm)
        for p in (A,B):
            self.assertFalse((p/"arm7").exists(),"No homegrown/custom ARM7")
            self.assertEqual(len(list((p/"source").glob("*.c"))),1)

if __name__=="__main__":
    unittest.main(verbosity=2)
