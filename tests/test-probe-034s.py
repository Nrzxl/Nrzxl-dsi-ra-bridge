"""Source gates of 034S, plus physically booted R0 identity."""
from pathlib import Path
import unittest
D=Path(__file__).resolve().parents[1]/"dsi"
R0=D/"probe-034r-control"
S0=D/"probe-034s-control"
S1=D/"probe-034s-twl-canary"
S2=D/"probe-034s-aes-symbol"
S3=D/"probe-034s-sdio-symbol"
def read(p,k):return (p/k).read_text()
class Gate034S(unittest.TestCase):
    def test_r0_s0_control_sources_equal(self):
        for name in ("source/main.c","arm7/source/main.c","arm7/Makefile"):
            self.assertEqual(read(R0,name),read(S0,name))
    def test_arm9_all_identical(self):
        for p in (S0,S1,S2,S3):
            self.assertEqual(read(R0,"source/main.c"),read(p,"source/main.c"))
    def test_single_canary_no_call(self):
        c=read(S1,"arm7/source/main.c")
        self.assertIn('section(".twl.text")',c)
        self.assertIn("dsirb_034s_twl_canary_ref",c)
        self.assertNotIn("dsirb_034s_twl_canary();",c)
        self.assertEqual(read(S0,"arm7/Makefile"),read(S1,"arm7/Makefile"))
    def test_s2_s3_library_only(self):
        base=read(S0,"arm7/source/main.c")
        for p in (S2,S3):
            self.assertEqual(base,read(p,"arm7/source/main.c"))
            self.assertIn("-ldswifi7 -lnds7",read(p,"arm7/Makefile"))
        self.assertIn("--undefined=mbedtls_internal_aes_encrypt",read(S2,"arm7/Makefile"))
        self.assertIn("--undefined=wifi_sdio_send_command",read(S3,"arm7/Makefile"))
        self.assertNotIn("wifi_sdio_send_command",read(S2,"arm7/Makefile"))
        self.assertNotIn("mbedtls_internal_aes_encrypt",read(S3,"arm7/Makefile"))
    def test_no_wifi_calls_or_disk_or_hardware_changes(self):
        for p in (S0,S1,S2,S3):
            src=read(p,"source/main.c")+read(p,"arm7/source/main.c")
            for ban in ("Wifi_Update();","Wifi_TWL_Update();",
                        "installWifiFIFO();","Wifi_Init(","Wifi_ConnectAP(",
                        "fatInitDefault(","fopen(","fwrite(","socket(",
                        "REG_MBK","REG_SCFG","nds-bootstrap","rcheevos",
                        "systemReboot("):
                self.assertNotIn(ban,src)
if __name__=="__main__":
    unittest.main(verbosity=2)
