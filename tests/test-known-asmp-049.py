"""049 tests: synthetic 4MiB only; no ROM or RA."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("known049",ROOT/"scripts"/"inspect-asmp-known-049.py")
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def sample(folder, header="ASMP"):
    base=folder/"DSi048_ASMP_SYNTHETIC_42"
    out=[]
    for label, frame, val in (("before",10,4),("idle",20,4),("after",30,5)):
        p=Path(str(base)+"_"+label+".bin")
        mem=bytearray(4194304)
        mem[0x09F358]=val
        mem[0x09F2F4]=4
        p.write_bytes(mem)
        meta={"format":"DSIRB048_BIZHAWK_RAM_V1","game_code":header,
          "rom_check":"HEADER_MATCH_ONLY" if header=="ASMP" else "UNVERIFIED",
          "rom_domain":"CartROM","ram_domain":"Main RAM",
          "label":label,"frame_before":frame,"frame_after":frame,
          "bytes":4194304,"real_emulator_capture":False,
          "dsi_physical":False,"official_awards_sent":False}
        p.with_suffix(".json").write_text(json.dumps(meta))
        out.append(p)
    return out

class Tests(unittest.TestCase):
    def test_catalog(self):
        d=mod.reference()
        self.assertEqual(d["game_code"],"ASMP")
        self.assertEqual(len(d["entries"]),8)
        self.assertTrue(d["safety"]["ra_awards_disabled"])
        self.assertEqual(d["entries"][0]["address_hex"],"0x0209F358")
        self.assertFalse(d["entries"][0]["width_provisional"])
        for e in d["entries"][1:]:
            self.assertTrue(e["width_provisional"])

    def test_real_address_in_synthetic_frame(self):
        with tempfile.TemporaryDirectory() as temp:
            result=mod.inspect(sample(Path(temp)),"coin_up",hud_before=4,hud_after=5)
            self.assertFalse(result["official_awards_sent"])
            self.assertFalse(result["active_emulator_rom_hash_verified"])
            self.assertFalse(result["dsi_physical_tested"])
            self.assertEqual(result["raw_dump_bytes_in_report"],0)
            self.assertEqual(len(result["rows"]),8)
            coin=result["rows"][0]
            self.assertEqual([coin["before"],coin["idle"],coin["after"]],[4,4,5])
            self.assertTrue(coin["hud_matches_memory"])

    def test_mismatch_hud_not_confirmed(self):
        with tempfile.TemporaryDirectory() as temp:
            row=mod.inspect(sample(Path(temp)),"coin_up",hud_before=3,hud_after=4)["rows"][0]
            self.assertFalse(row["hud_matches_memory"])

    def test_unverified_block_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            p=sample(Path(temp),"UNVERIFIED")
            with self.assertRaisesRegex(mod.KnownError,"header"):
                mod.inspect(p,"coin_up")
            self.assertFalse(mod.inspect(p,"coin_up",allow_unverified=True)["asmp_header_only"])

    def test_mixed_session_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            p=sample(Path(temp))
            q=Path(temp)/"DIFFERENT_after.bin"
            q.write_bytes(p[2].read_bytes())
            q.with_suffix(".json").write_bytes(p[2].with_suffix(".json").read_bytes())
            with self.assertRaisesRegex(mod.KnownError,"Mixed"):
                mod.inspect((p[0],p[1],q),"coin_up")

    def test_repeated_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            p=sample(Path(temp))
            out=Path(temp)/"report.json"
            out.write_text("ORIGINAL")
            old=sys.argv
            try:
                sys.argv=["test","--before",str(p[0]),"--idle",str(p[1]),
                  "--after",str(p[2]),"--event","coin_up","--out",str(out)]
                with self.assertRaises(SystemExit): mod.main()
            finally: sys.argv=old
            self.assertEqual(out.read_text(),"ORIGINAL")

    def test_lua_reads_only(self):
        code=(ROOT/"lab"/"bizhawk-asmp-eu-live-watch-049.lua").read_text()
        for bad in ("memory.write_","joypad.set","savestate.save","socket.","http."):
            self.assertNotIn(bad,code)
        self.assertIn("memory.read_bytes_as_binary_string",code)
        self.assertNotIn('type(memory.read_u8)',code)
        self.assertNotIn('type(memory.read_u16_le)',code)
        self.assertIn("string.byte(bytes, 1)",code)
        self.assertIn("string.byte(bytes, 2)",code)
        self.assertIn("emu.frameadvance()",code)
        self.assertIn("0x09F358",code)

if __name__=="__main__": unittest.main(verbosity=2)
