"""050 PC-only synthetic safety checks, no ROM/DSi/RA credentials."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LUA=ROOT/"lab"/"bizhawk-asmp-eu-events-050.lua"
WORKFLOW=ROOT/".github"/"workflows"/"asmp-eu-pc-events-050.yml"
CATALOG=ROOT/"research"/"asmp-eu-known-addresses-049.json"

class DetectorSourceTests(unittest.TestCase):
    def test_catalog_gates(self):
        d=json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertTrue(d["safety"]["ra_awards_disabled"])
        self.assertFalse(d["safety"]["dsi_physical_tested"])
    def test_no_writes_or_network(self):
        s=LUA.read_text(encoding="utf-8")
        for name in ("memory.write_","savestate.save","joypad.set",
                     "socket.","http.","memory.writedword","memory.writebyte"):
            self.assertNotIn(name,s)
        for name in ("0x09F358","0x11117C","0x092144","0x09F2F8",
                     "read_bytes_as_binary_string","read_bytes_as_array",
                     "memory.read_u8","memory.readbyte","ASMP header missing/contradicted",
                     "NO RA AWARD"):
            self.assertIn(name,s)
    def test_guard_and_sync(self):
        s=LUA.read_text(encoding="utf-8")
        for name in ("WARMUP_FRAMES, PAIR_WINDOW, COIN_WINDOW = 45, 2, 2",
                     "now.alt==now.hp*256+128",
                     "math.abs(hp_change-alt_change)<=PAIR_WINDOW",
                     "frame-last_coin_frame<=COIN_WINDOW",
                     "PHASE_TRANSITION_OBSERVED","DAMAGE_OBSERVED",
                     "HEALTH_RECOVERY_COIN_CORRELATED","HEALTH_RECOVERY_UNATTRIBUTED"):
            self.assertIn(name,s)
    def test_package_excludes_roms(self):
        s=WORKFLOW.read_text(encoding="utf-8")
        for x in ("PC-only","tests/mock-asmp-eu-events-050.lua",
                  "tests/test-asmp-events-050.py","*.nds","*.bin"):
            self.assertIn(x,s)

if __name__=="__main__":
    unittest.main(verbosity=2)
