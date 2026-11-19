"""034O regression dissection: one independent variable per step, no DSWiFi."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DSI=ROOT/"dsi"
L0=DSI/"probe-034l-control"
O0=DSI/"probe-034o-ui"
O1=DSI/"probe-034o-send"
O2=DSI/"probe-034o-receive"

def rd(folder,sub):
    return (folder/sub).read_text()

class FIFO034O(unittest.TestCase):
    def test_known_arm7_control_exactly_reused(self):
        self.assertEqual(rd(O0,"arm7/source/main.c"),rd(L0,"arm7/source/main.c"))
        self.assertEqual(rd(O0,"arm7/Makefile"),rd(L0,"arm7/Makefile"))

    def test_only_arm7_changes_between_o0_and_o1(self):
        self.assertEqual(rd(O0,"source/main.c"),rd(O1,"source/main.c"))
        self.assertEqual(rd(O0,"arm7/Makefile"),rd(O1,"arm7/Makefile"))
        source=rd(O0,"arm7/source/main.c")
        sent=rd(O1,"arm7/source/main.c")
        stage1="""    /* 034O stage 1: send only; ARM9 may not yet be polling. */
    fifoSendValue32(FIFO_USER_03, 0x4E370001u);

"""
        stage2="""    /* 034O stage 2: send only after normal IRQ setup. */
    fifoSendValue32(FIFO_USER_03, 0x4E370002u);
"""
        self.assertEqual(sent.replace(stage1,"").replace(stage2,""),source)
        self.assertNotIn("fifoSendValue32(FIFO_USER_03",source)
        self.assertEqual(sent.count("fifoSendValue32(FIFO_USER_03"),2)

    def test_only_rx_switch_changes_o1_and_o2(self):
        self.assertEqual(rd(O1,"arm7/source/main.c"),rd(O2,"arm7/source/main.c"))
        a=rd(O1,"source/main.c")
        b=rd(O2,"source/main.c")
        self.assertEqual(a.replace("#define DSIRB_ENABLE_RX 0","#define DSIRB_ENABLE_RX 1"),b)
        self.assertIn("#if DSIRB_ENABLE_RX",a)
        self.assertIn("fifoCheckValue32(FIFO_USER_03)",a)
        self.assertIn("fifoGetValue32(FIFO_USER_03)",a)
        self.assertIn("n < 4",a)  # avoid unbounded receive loop
        self.assertIn("MAIN REACHED: YES",a)
        self.assertIn("LOOP ALIVE:",a)
        self.assertIn("KEY_START",a)

    def test_no_wifi_network_sd_firmware_or_retail(self):
        for p in (O0,O1,O2):
            m=rd(p,"Makefile")
            am=rd(p,"arm7/Makefile")
            arm9=rd(p,"source/main.c")
            arm7=rd(p,"arm7/source/main.c")
            self.assertIn("rom_arm9/Makefile",m)
            self.assertIn("rom_arm9arm7/Makefile.arm7",am)
            self.assertIn("-lnds7",am)
            self.assertNotIn("-ldswifi",am)
            self.assertIn("SPDX-License-Identifier: Zlib",arm7)
            for forbidden in ("#include <dswifi","-ldswifi",
                    "installWifiFIFO(", "Wifi_Update(", "Wifi_InitDefault(",
                    "Wifi_ConnectAP(", "Wifi_AutoConnect(", "fatInitDefault(",
                    "fopen(", "fwrite(", "mkdir(", "socket(", "connect(",
                    "nds-bootstrap", "chainload(", "session_login(", "rcheevos",
                    "REG_SCFG", "REG_MBK", "swiSoftReset(", "systemReboot("):
                self.assertNotIn(forbidden,arm9+arm7+m+am)

if __name__ == "__main__":
    unittest.main(verbosity=2)
