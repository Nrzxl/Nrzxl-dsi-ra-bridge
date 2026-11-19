"""Source evidence of one-round 040; no physical or network execution."""
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
class TestRecovery040(unittest.TestCase):
    def test_recovered_033_launcher_requires_dsi_sd_and_crc(self):
        s=(ROOT/"dsi/launcher-033-gpl/source/main.c").read_text()
        for needle in ('!isDSiMode()', 'stat("sd:/",', 'fatInitDefault()',
                       "Fixture integrity PASS", "runNdsFile(path,1,args)"):
            self.assertIn(needle,s)
    def test_recovered_observer_fixture_does_not_require_wifi(self):
        s=(ROOT/"dsi/fixture-033/source/main.c").read_text()
        for needle in ('sd:/DSiRABridge_033', '"DSIOBS33"', '0xD000',
                       'game_vblank','fatInitDefault()'):
            self.assertIn(needle,s)
        self.assertNotIn("Wifi_InitDefault(",s)
        self.assertNotIn("Wifi_TWL_Update(",s)
    def test_physical_evidence_not_renamed_emulator_pass(self):
        d=(ROOT/"docs/recovery-040.md").read_text()
        self.assertIn("DSi física NOT_RUN",d)
        self.assertIn("NDS_EMULATOR",d)
        self.assertIn("LOCAL_TEST_ONLY",d)
if __name__=="__main__":unittest.main(verbosity=2)
