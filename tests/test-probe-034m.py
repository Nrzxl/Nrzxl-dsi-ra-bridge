"""034M: compare official BlocksDS 1.25.0 minimal versus WiFi ARM7 without runtime requests."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/"dsi"
A=ROOT/"probe-034m-base125"
W=ROOT/"probe-034m-wifi125"

class Official034M(unittest.TestCase):
    def test_identical_arm9(self):
        a=(A/"source/main.c").read_bytes()
        b=(W/"source/main.c").read_bytes()
        self.assertEqual(a,b)
        self.assertIn(b"MAIN REACHED: YES",a)
        self.assertIn(b"LOOP ALIVE:",a)
        self.assertIn(b"KEY_START",a)

    def test_official_prebuilt_no_custom_core(self):
        m0=(A/"Makefile").read_text()
        m1=(W/"Makefile").read_text()
        self.assertIn("main_core/arm7_minimal.elf",m0)
        self.assertIn("main_core/arm7_dswifi.elf",m1)
        self.assertIn("rom_arm9/Makefile",m0)
        self.assertIn("rom_arm9/Makefile",m1)
        for path in (A,W):
            self.assertFalse((path/"arm7").exists())
            self.assertEqual(len(list((path/"source").glob("*.c"))),1)
            self.assertIn("LIBS          := -lnds9",(path/"Makefile").read_text())

    def test_no_hardware_mutations_network_sd_games(self):
        s=(A/"source/main.c").read_text()
        for banned in ("Wifi_InitDefault(","Wifi_AutoConnect(","Wifi_ConnectAP(",
             "Wifi_Update(","installWifiFIFO(", "fatInitDefault(", "fopen(",
             "mkdir(", "fwrite(", "socket(", "connect(", "chainload(",
             "nds-bootstrap", "session_login(", "rcheevos", "REG_MBK",
             "REG_SCFG", "swiSoftReset(", "systemReboot("):
            self.assertNotIn(banned,s)
if __name__=="__main__":unittest.main(verbosity=2)
