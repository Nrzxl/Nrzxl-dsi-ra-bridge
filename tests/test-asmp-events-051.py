"""051 safety checks (synthetic only; all hardware/official awards remain disabled)."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"lab"/"bizhawk-asmp-eu-events-051.lua"
WORKFLOW=ROOT/".github"/"workflows"/"asmp-eu-pc-events-051.yml"
CATALOG=ROOT/"research"/"asmp-eu-known-addresses-049.json"

class Validator051(unittest.TestCase):
    def test_legacy_catalog_never_claims_physical_or_official(self):
        m=json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertTrue(m["safety"]["ra_awards_disabled"])
        self.assertFalse(m["safety"]["dsi_physical_tested"])
    def test_only_reads_no_credentials_or_awards(self):
        s=SRC.read_text(encoding="utf-8")
        for bad in ("memory.write_","memory.writebyte","joypad.set",
                    "savestate.save","socket.","http.","rc_client",
                    "official_award(","io.open(","os.execute("):
            self.assertNotIn(bad,s)
        for required in ("read_bytes_as_binary_string","read_bytes_as_array",
                         "memory.read_u8","memory.readbyte",
                         "ASMP cartridge header absent/contradicted",
                         "NO RA AWARD","0x09F358","0x09F2F4",
                         "0x09F2F8","0x11117C","0x092144","0x09CAE1"):
            self.assertIn(required,s)
    def test_safety_guards_and_heuristic_labels(self):
        s=SRC.read_text(encoding="utf-8")
        for required in ("WARMUP, PAIR_WINDOW, COIN_WINDOW = 45, 2, 2",
                         "STABLE_CANDIDATE_FRAMES = 3",
                         "s.hp==7 or s.hp==8",
                         "FRAME_DISCONTINUITY",
                         "LIVES_DROP_STABLE_CANDIDATE",
                         "CHARACTER_VALUE_STABLE_CANDIDATE",
                         "HEALTH_PAIR_TIMEOUT",
                         "PHASE_TRANSITION_OBSERVED",
                         "HEALTH_RECOVERY_COIN_CORRELATED",
                         "HEALTH_RECOVERY_UNATTRIBUTED"):
            self.assertIn(required,s)
        self.assertNotIn("Yoshi = 3",s)
        self.assertNotIn("LIFE_LOST_CONFIRMED",s)
    def test_workflow_does_not_package_rom_or_secrets(self):
        y=WORKFLOW.read_text(encoding="utf-8")
        for required in ("PC-only","mock-asmp-eu-events-051.lua",
                         "test-asmp-events-051.py","*.nds","*.bin","*.sav",
                         "NO_DSi"):
            self.assertIn(required,y)

if __name__=="__main__":
    unittest.main(verbosity=2)
