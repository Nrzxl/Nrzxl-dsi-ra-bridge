"""Read-only safety gate: official minimal vs WiFi-only ARM7 cores."""
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]/"dsi"
A=ROOT/"probe-034k-minimal"
B=ROOT/"probe-034k-wifi-only"

class Official034K(unittest.TestCase):
    def test_arm9_identical(self):
        code=(A/"source/main.c").read_text()
        self.assertEqual(code,(B/"source/main.c").read_text())
        self.assertIn("MAIN REACHED: YES",code)
        self.assertIn("LOOP ALIVE:",code)
        for x in ("Wifi_InitDefault(","Wifi_AutoConnect(","Wifi_ConnectAP(",
                  "installWifiFIFO(","Wifi_Update(","fatInitDefault(","fopen(",
                  "fwrite(","mkdir(","socket(","connect(","chainload(",
                  "rcheevos","nds-bootstrap","REG_SCFG","swiSoftReset("):
            self.assertNotIn(x,code)

    def test_official_prebuilt_cores_without_custom_arm7(self):
        am=(A/"Makefile").read_text()
        bm=(B/"Makefile").read_text()
        self.assertIn("/sys/arm7/main_core/arm7_minimal.elf",am)
        self.assertIn("/sys/arm7/main_core/arm7_dswifi.elf",bm)
        self.assertIn("rom_arm9/Makefile",am)
        self.assertIn("rom_arm9/Makefile",bm)
        for p in (A,B):
            self.assertFalse((p/"arm7").exists())
            self.assertEqual(len(list((p/"source").glob("*.c"))),1)

if __name__=="__main__":
    unittest.main(verbosity=2)
