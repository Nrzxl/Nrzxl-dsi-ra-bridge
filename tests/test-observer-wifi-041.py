"""041 preserves the 033 external hook and 030 wire; no official awards."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
def s(x):return (R/x).read_text()
class Integration041(unittest.TestCase):
    def test_external_hook_is_still_not_in_game(self):
        fixture=s("dsi/fixture-041/source/main.c")
        hook=s("dsi/observer-041/observer.c")
        self.assertIn("void game_vblank(void)",fixture)
        self.assertIn("void observer_sample(void)",hook)
        self.assertNotIn("observer_sample(",fixture)
        self.assertIn("if(s->stored>=OBS_CAPACITY)return;",hook)
        self.assertIn("s->reserved[0]=(seq+2u)&~1u",hook)
    def test_network_observer_only_fail_closed(self):
        net=s("dsi/fixture-041/source/network041.c")
        for x in ('memcmp((const void*)OBS_HEADER,"DSIOBS33",8)',
                  'if(!observer_ready())','if(!config_read())',
                  'Wifi_InitDefault(INIT_ONLY)','wfcBeginAutoConnect()',
                  'wire_control(packet,"DSH3"','wire_sample(packet,1,mode',
                  'const volatile uint32_t *h=',
                  'if(a!=b||b&1u||!valid',
                  'if(sendto(fd,packet,64'):
            self.assertIn(x,net)
        self.assertNotIn("Wifi_TWL_Update();",net)
        self.assertNotIn("installWifiFIFO();",net)
        self.assertNotIn("fwrite(",net)
        self.assertIn('if(keys&KEY_Y)network041_start();',s("dsi/fixture-041/source/main.c"))
    def test_pinned_fixture_and_nand_guard(self):
        launcher=s("dsi/launcher-041-gpl/source/main.c")
        for x in ('!isDSiMode()','stat("sd:/",','Fixture integrity PASS',
                  "runNdsFile(path,1,args)",
                  "Fixture_B_041_observed.nds"):
            self.assertIn(x,launcher)
        script=s("scripts/build-independent-041.sh")
        self.assertIn("NAND crypto register repair intentionally omitted",script)
        self.assertIn("devkitpro",s(".github/workflows/observer-wifi-041.yml"))
        self.assertNotIn("REG_SCFG",s("dsi/fixture-041/source/network041.c"))
    def test_observer_binary_compatible(self):
        old=s("dsi/observer-033/entry.s")
        new=s("dsi/observer-041/entry.s")
        self.assertEqual(old,new)
        self.assertIn('module[:8]==b"DSIOBS33"',s("scripts/instrument-fixture-041.py"))
        self.assertIn('b"DSI_RA_INDEPENDENT_FIXTURE_041"',s("scripts/instrument-fixture-041.py"))
    def test_030_wire_unmodified(self):
        self.assertEqual(s("dsi/network/include/wire.h"),s("dsi/fixture-041/include/wire.h"))
        self.assertEqual(s("dsi/network/include/wire.h"),s("dsi/network-032/include/wire.h"))
if __name__=="__main__":unittest.main(verbosity=2)
