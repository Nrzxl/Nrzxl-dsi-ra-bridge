"""034R physical control safety and one-target-symbol-per-variant tests."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/"dsi"
P0=ROOT/"probe-034p-control"
R0=ROOT/"probe-034r-control"
R1=ROOT/"probe-034r-ntr-link"
R2=ROOT/"probe-034r-twl-link"

def get(root,part):return (root/part).read_bytes()

class SymbolSplit(unittest.TestCase):
    def test_control_preserved_from_physical_p0(self):
        for part in ("source/main.c","arm7/source/main.c","arm7/Makefile"):
            self.assertEqual(get(P0,part),get(R0,part))
    def test_arm9_byte_identical_all(self):
        for x in (R0,R1,R2):
            self.assertEqual(get(P0,"source/main.c"),get(x,"source/main.c"))
        self.assertIn(b"STAGE 1: %-7s",get(P0,"source/main.c"))
        self.assertIn(b"STAGE 2: %-7s",get(P0,"source/main.c"))
    def test_ntr_twl_exclusive_link_only(self):
        a=get(R0,"arm7/source/main.c").decode()
        b=get(R1,"arm7/source/main.c").decode()
        c=get(R2,"arm7/source/main.c").decode()
        self.assertIn("= Wifi_NTR_Update;",b)
        self.assertIn("= Wifi_TWL_Update;",c)
        self.assertNotIn("Wifi_TWL_Update",b)
        self.assertNotIn("Wifi_NTR_Update",c)
        self.assertNotIn("Wifi_NTR_Update",a)
        for z in (b,c):
            self.assertIn("dsirb_034r_symbol_pointer",z)
            self.assertIn('volatile (""',z)
            self.assertNotIn("Wifi_Update();",z)
            self.assertNotIn("installWifiFIFO();",z)
            self.assertNotIn("Wifi_Init(",z)
        self.assertEqual(b.replace("Wifi_NTR_Update","FUNCTION"),c.replace("Wifi_TWL_Update","FUNCTION"))
    def test_only_wifi_archive_added_on_arm7(self):
        self.assertNotIn(b"-ldswifi7",get(R0,"arm7/Makefile"))
        for x in (R1,R2):
            self.assertIn(b"-ldswifi7 -lnds7",get(x,"arm7/Makefile"))
            self.assertIn(b"$(BLOCKSDS)/libs/dswifi",get(x,"arm7/Makefile"))
        for x in (R0,R1,R2):
            s=get(x,"source/main.c")+get(x,"arm7/source/main.c")
            for banned in (b"Wifi_InitDefault(",b"Wifi_ConnectAP(",b"fatInitDefault(",
                     b"socket(",b"fopen(",b"REG_MBK",b"REG_SCFG",b"rcheevos",
                     b"nds-bootstrap",b"swiSoftReset(",b"systemReboot("):
                self.assertNotIn(banned,s)

if __name__=="__main__":unittest.main(verbosity=2)
