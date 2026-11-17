import unittest,importlib.util,struct,zlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
patch=module("patch","scripts/instrument-fixture-033.py")
dec=module("decoder","windows/observer-033/decode.py")
def fixture():
    b=bytearray(0x1200);b[0x300:0x300+len(b"DSI_RA_INDEPENDENT_FIXTURE_033")]=b"DSI_RA_INDEPENDENT_FIXTURE_033"
    struct.pack_into("<4I",b,0x20,0x200,0x02000000,0x02000000,0x1000)
    struct.pack_into("<4I",b,0x30,0x1000,0x03800000,0x03800000,0x100)
    struct.pack_into("<I",b,0x240,patch.PUSH)
    struct.pack_into("<H",b,0x15e,patch.crc16(b[:0x15e]))
    m=bytearray(128);m[:8]=b"DSIOBS33"
    return b,dict(game_vblank=0x02000040,game_state=0x02000800),m,dict(observer_entry=patch.BASE+64,observer_resume=patch.BASE+120)
def capture():
    b=bytearray(0xD000);b[:8]=b"DSIOBS33"
    struct.pack_into("<14I",b,8,1,64,20,0x02000800,0x02000040,0x02000044,0x02203000,32,1200,0x02202000,0x0221C000,0x02220000,patch.PUSH,0)
    struct.pack_into("<9I",b,0x2000,1800,0,1200,0,1799,0,0x0221FF00,0,0)
    for i in range(1200):
        pos=0x3000+i*32;struct.pack_into("<7I",b,pos,i,i*2,i,0,i^0x9317A55A,0,1);struct.pack_into("<I",b,pos+28,zlib.crc32(b[pos:pos+28]))
    return b
class Tests(unittest.TestCase):
    def test_whitelist_full_nds(self):
        b,s,m,ms=fixture();out,e=patch.instrument(b,s,m,ms)
        self.assertEqual(out[0x1000:0x1100],b[0x1000:0x1100]);self.assertEqual(struct.unpack_from("<I",out,0x24)[0],0x02000000)
        self.assertEqual(e["arm9_expanded_size"],0x220000);self.assertNotEqual(out,b)
    def test_unknown_rejected(self):
        b,s,m,ms=fixture();b[0x300:0x340]=bytes(64)
        with self.assertRaises(ValueError):patch.instrument(b,s,m,ms)
    def test_unknown_instruction(self):
        b,s,m,ms=fixture();struct.pack_into("<I",b,0x240,0xE1A00000)
        with self.assertRaises(ValueError):patch.instrument(b,s,m,ms)
    def test_arm7_overlap(self):
        b,s,m,ms=fixture();struct.pack_into("<I",b,0x38,patch.BASE);struct.pack_into("<H",b,0x15e,patch.crc16(b[:0x15e]))
        with self.assertRaises(ValueError):patch.instrument(b,s,m,ms)
    def test_watch_bounds(self):
        b,s,m,ms=fixture();s["game_state"]=0x04000000
        with self.assertRaises(ValueError):patch.instrument(b,s,m,ms)
    def test_header_crc(self):
        b,s,m,ms=fixture();b[0]^=1
        with self.assertRaises(ValueError):patch.instrument(b,s,m,ms)
    def test_synthetic_integrity(self):
        r=dec.decode(capture(),"SYNTHETIC_TEST");self.assertEqual(r["frames_observed"],1800);self.assertFalse(r["submitted"])
    def test_record_corruption(self):
        b=capture();b[0x3000+40]^=1
        with self.assertRaises(ValueError):dec.decode(b,"SYNTHETIC_TEST")
    def test_stopped_observer(self):
        b=capture();struct.pack_into("<I",b,0x2000,1200)
        with self.assertRaises(ValueError):dec.decode(b,"SYNTHETIC_TEST")
    def test_guard(self):
        b=capture();struct.pack_into("<I",b,0x201c,1)
        with self.assertRaises(ValueError):dec.decode(b,"SYNTHETIC_TEST")
    def test_provenance(self):
        with self.assertRaises(ValueError):dec.decode(capture(),"hardware")
    def test_independent_source(self):
        s=(ROOT/"dsi/fixture-033/source/main.c").read_text()
        self.assertNotIn("observer_sample",s);self.assertNotIn("observer_entry",s);self.assertIn("irqSet(IRQ_VBLANK,game_vblank)",s)
if __name__=="__main__":unittest.main()
