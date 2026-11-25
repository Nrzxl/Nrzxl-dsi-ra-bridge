"""DSi 052 one-pass read-only observer static tests (not a real-game test)."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LUA=ROOT/"lab"/"bizhawk-asmp-eu-observer-052.lua"
WORKFLOW=ROOT/".github"/"workflows"/"asmp-eu-onepass-observer-052.yml"
class Safety052(unittest.TestCase):
 def test_only_known_eu_watch_windows(self):
  s=LUA.read_text(encoding="utf-8")
  for v in ["0x09CAB4,15","0x09CAD2,15","0x09CAA7",
            "0x09F394","0x09F30C","0x09F310","0x09CAE1",
            "0x09F2F4","0x11117C","0x092144","0x09F358"]:
   self.assertIn(v,s)
 def test_no_cheats_telemetry_or_unsafe_memory_ops(self):
  s=LUA.read_text(encoding="utf-8")
  for bad in ["memory.write_","memory.writebyte","joypad.set",
              "savestate.save","socket.","http.","rc_client",
              "os.execute(","os.remove(","os.rename("]:
   self.assertNotIn(bad,s)
  self.assertIn("ptr+8>=0x02400000",s)
  self.assertIn("ptr%4~=0",s)
  self.assertIn("PC_JOURNAL",s)
  self.assertIn("GAME_OVER_RESET_CANDIDATE",s)
  self.assertIn("STAR_FLAG_STABLE_GAIN_CANDIDATE",s)
  self.assertIn("CAP_OR_EFFECTIVE_CHARACTER_CANDIDATE",s)
 def test_package_excludes_private_rom_data(self):
  y=WORKFLOW.read_text(encoding="utf-8")
  for v in ["PC-only","mock-asmp-eu-observer-052.lua",
            "test-asmp-observer-052.py","*.nds","*.bin","*.sav","NO_DSi"]:
   self.assertIn(v,y)
if __name__=="__main__":unittest.main(verbosity=2)
