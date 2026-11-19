"""DSi 043 - deterministic synthetic tests only; no game files, tokens, NAND or network."""
import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod
p=load("prepare043",ROOT/"scripts/prepare-offline-game-043.py")
patch=load("patch043",ROOT/"scripts/patch-offline-retail-043.py")
p42=load("preflight042",ROOT/"scripts/retail-preflight-042.py")

def fake_rom(path,missing_banner=False):
    size=0x3000
    b=bytearray(size)
    b[:11]=b"S.MARIO64DS"
    b[12:16]=b"ASMP"
    b[0x12]=0
    struct.pack_into("<4I",b,0x20,0x200,0x02000000,0x02000000,0x600)
    struct.pack_into("<4I",b,0x30,0x800,0x03800000,0x03800000,0x200)
    struct.pack_into("<I",b,0x68,0x2400 if not missing_banner else size-0x100)
    struct.pack_into("<H",b,0x15E,p42.crc16(b[:0x15E]))
    for i in range(0x200,0xA00):b[i]=(i*17)%256
    for i in range(0x2400,size):b[i]=(i*31)%256
    path.write_bytes(b)
    return b

def fake_bin(path,module=False):
    if module:
        b=bytearray(2048);b[:4]=b"DSCV";struct.pack_into("<I",b,4,7)
    else:
        b=bytearray(4096);b[:12]=b"NDSBOOTSTRAP";b[12:16]=b"KBSE"
    path.write_bytes(b)
    return hashlib.sha256(b).hexdigest()

class Offline043(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.root=Path(self.t.name)
        self.rom=self.root/"mario.nds"
        fake_rom(self.rom)
        self.report=self.root/"preflight.json"
        self.report.write_text(json.dumps(p42.analyze(self.rom,True)))
        self.bs=self.root/"bootstrap.nds"
        self.mod=self.root/"module.bin"
        bsh=fake_bin(self.bs)
        modh=fake_bin(self.mod,True)
        self.man=self.root/"build-manifest.json"
        self.man.write_text(json.dumps({"format":p.EXPECTED_FMT,"offline_gates_passed":True,
           "source_bootstrap":p.BOOT_PIN,"source_dscheevos":p.DSCHEEVOS_PIN,
           "source_rcheevos":p.RC_PIN,"bootstrap_sha256":bsh,"module_sha256":modh}))
    def tearDown(self):self.t.cleanup()
    def pack(self,out=None):
        return p.prepare(self.rom,self.report,self.bs,self.mod,self.man,out or self.root/"stage")
    def test_hash_recipe_reconstructs_exact_ranges(self):
        b=self.rom.read_bytes()
        m=hashlib.md5()
        m.update(b[:0x160])
        m.update(b[0x200:0x800])
        m.update(b[0x800:0xA00])
        m.update(b[0x2400:0x2E00])
        self.assertEqual(p.ra_hash_ds(self.rom),m.hexdigest())
    def test_short_banner_padded_like_rcheevos(self):
        fake_rom(self.rom,True)
        m=hashlib.md5()
        b=self.rom.read_bytes()
        m.update(b[:0x160]);m.update(b[0x200:0x800]);m.update(b[0x800:0xA00])
        m.update(b[0x2F00:]);m.update(bytes(0x900))
        self.assertEqual(p.ra_hash_ds(self.rom),m.hexdigest())
    def test_session_hard_offline_and_qa_only(self):
        h=p.ra_hash_ds(self.rom)
        data=p.make_session(p.GAME_PATH,h,now=1234)
        self.assertTrue(p.verify_session(data,h))
        self.assertEqual(data[0x1CD],0)
        self.assertEqual(data[0x1CE],1)
        self.assertEqual(data[0x1F6],0)
        self.assertEqual(data[0x16C:0x1AC],bytes(64))
        self.assertIn(b"LOCAL QA ONLY",data)
        self.assertNotIn(b"awardachievement",data)
        self.assertNotIn(b"password",data.lower())
    def test_modified_session_fail_closed(self):
        h=p.ra_hash_ds(self.rom)
        for off,val in [(0x1CD,1),(0x1CE,0),(0x1F6,1),(0x16C,ord("x"))]:
            with self.subTest(off=off):
                b=bytearray(p.make_session(p.GAME_PATH,h))
                b[off]=val
                with self.assertRaises(ValueError):
                    p.verify_session(b,h)
    def test_staging_isolated_from_original_and_idempotence_refused(self):
        original=self.rom.read_bytes()
        result=self.pack()
        self.assertEqual(result["status"],"STAGED_OFFLINE_043_FOR_SPARE_SD_ONLY")
        self.assertEqual(original,self.rom.read_bytes())
        self.assertEqual((self.root/"stage/SD_ROOT/DSiRABridge_043/mario_europe.nds").read_bytes(),original)
        sess=(self.root/"stage/SD_ROOT/DSiRABridge_043/dscheevos/session.bin").read_bytes()
        self.assertTrue(p.verify_session(sess,result["ra_ds_hash"]))
        self.assertTrue((self.root/"stage/SD_ROOT/DSiRABridge_043/mario_test_only.sav").exists())
        self.assertFalse((self.root/"stage/SD_ROOT/_nds").exists())
        with self.assertRaisesRegex(ValueError,"already exists"):
            self.pack()
    def test_preflight_mismatch_fail_without_writing(self):
        self.rom.write_bytes(self.rom.read_bytes()+b"x")
        with self.assertRaisesRegex(ValueError,"ROM differs"):
            self.pack()
        self.assertFalse((self.root/"stage").exists())
    def test_untrusted_module_fail_without_writing(self):
        self.mod.write_bytes(self.mod.read_bytes()+b"x")
        with self.assertRaisesRegex(ValueError,"unexpected bytes"):
            self.pack()
        self.assertFalse((self.root/"stage").exists())
    def test_reject_wrong_game_code(self):
        b=bytearray(self.rom.read_bytes());b[12:16]=b"ASME";self.rom.write_bytes(b)
        with self.assertRaisesRegex(ValueError,"Expected EU"):
            self.pack()
    def test_patch_drift_hard_fail(self):
        with self.assertRaisesRegex(ValueError,"upstream drift"):
            patch.replace_once("x","missing","new","unit")
        with self.assertRaisesRegex(ValueError,"upstream drift"):
            patch.edit_range("start only","start","end","new","unit")

if __name__=="__main__":unittest.main(verbosity=2)
