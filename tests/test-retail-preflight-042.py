"""Offline-only proof that 042 cannot edit, accept corrupt ROM, or read arbitrary memory."""
import importlib.util,os,struct,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("pf042",ROOT/"scripts/retail-preflight-042.py")
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def make_nds(path,code=b"GAME",unit=0,arm9_ram=0x02000000,arm7_ram=0x03800000):
    h=bytearray(0xA00)
    h[:9]=b"Test Game"
    h[0xC:0x10]=code;h[0x12]=unit
    struct.pack_into("<4I",h,0x20,0x200,arm9_ram,arm9_ram,0x400)
    struct.pack_into("<4I",h,0x30,0x600,arm7_ram,arm7_ram,0x200)
    if unit==2:
        struct.pack_into("<4I",h,0x1C0,0x800,0x02020000,0x02020000,0x100)
    struct.pack_into("<H",h,0x15E,p.crc16(h[:0x15E]))
    path.write_bytes(h)
    return h
class Retail042(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory()
        self.path=Path(self.d.name)/"retail_test.nds"
        make_nds(self.path)
    def tearDown(self):self.d.cleanup()
    def test_readonly_ntr_guarded(self):
        before=self.path.read_bytes()
        d=p.analyze(self.path,True)
        self.assertEqual(d["gate"],"HEADER_ONLY_PASS_MORE_GATES_REQUIRED")
        self.assertFalse(d["observer_active"]);self.assertFalse(d["official_achievements"])
        self.assertFalse(d["actual_running_memory_compatible"] is True)
        self.assertEqual(d["sha256_original_rom"],__import__("hashlib").sha256(before).hexdigest())
        self.assertEqual(before,self.path.read_bytes())
    def test_corrupt_header_fail_closed(self):
        b=bytearray(self.path.read_bytes());b[20]^=0x23;self.path.write_bytes(b)
        with self.assertRaisesRegex(ValueError,"header CRC"):p.analyze(self.path)
    def test_out_of_file_segment(self):
        b=bytearray(self.path.read_bytes());struct.pack_into("<I",b,0x2C,0xFFFF0000)
        struct.pack_into("<H",b,0x15E,p.crc16(b[:0x15E]));self.path.write_bytes(b)
        with self.assertRaisesRegex(ValueError,"outside"):p.analyze(self.path)
    def test_reject_module_overlap(self):
        make_nds(self.path,arm9_ram=0x02D80000)
        self.assertEqual(p.analyze(self.path)["gate"],"BLOCKED_HEADER_RAM_OVERLAP")
    def test_dsi_mode_conservative(self):
        make_nds(self.path,unit=2)
        d=p.analyze(self.path)
        self.assertEqual(d["gate"],"BLOCKED_DSI_MODE_GAME_UNSUPPORTED_BY_RETAIL_PATH")
    def test_memory_map_watches(self):
        valid={"version":1,"watches":[{"address":"0x0","width":4},
                         {"address":"0x01000000","width":1}]}
        self.assertEqual(p.watchplan(valid)["count"],2)
        for address in [0x03FFFFF,0x0400000,0x01003FFF,0x02000000]:
            with self.subTest(address=address):
                with self.assertRaisesRegex(ValueError,"outside"):
                    p.watchplan({"version":1,"watches":[{"address":address,"width":4}]})
    def test_no_duplicate_or_unbounded_watch(self):
        with self.assertRaises(ValueError):p.watchplan({"version":1,"watches":[{"address":0,"width":1}]*2})
        with self.assertRaises(ValueError):p.watchplan({"version":1,"watches":[{"address":i,"width":1} for i in range(33)]})
    def test_no_output_overwrite(self):
        import subprocess,sys
        old=self.path.read_bytes()
        x=subprocess.run([sys.executable,str(ROOT/"scripts/retail-preflight-042.py"),
                         str(self.path),"--output",str(self.path)],capture_output=True,text=True)
        self.assertNotEqual(x.returncode,0)
        self.assertEqual(self.path.read_bytes(),old)
if __name__=="__main__":unittest.main(verbosity=2)
