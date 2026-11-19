import importlib.util,struct,unittest
from pathlib import Path
src=Path(__file__).resolve().parents[1]/"scripts/validate-retail-nds-042.py"
s=importlib.util.spec_from_file_location("ndsvalid",src)
v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def sample():
 b=bytearray(0x900);b[:12]=b"nds-bootstra";b[12:16]=b"KBSE";b[0x12]=0
 struct.pack_into("<4I",b,0x20,0x200,0x02000000,0x02000000,0x300)
 struct.pack_into("<4I",b,0x30,0x600,0x03800000,0x03800000,0x100)
 struct.pack_into("<H",b,0x15e,v.crc16(b[:0x15e]))
 return b
class NDS042(unittest.TestCase):
 def test_valid(self):
  self.assertEqual(v.validate(sample())["status"],"NDS_HEADER_SEGMENTS_VALIDATED_NOT_BOOTED")
 def test_crc(self):
  b=sample();b[0x40]^=1
  with self.assertRaisesRegex(ValueError,"CRC"):v.validate(b)
 def test_wrong_game(self):
  b=sample();b[0]=0
  with self.assertRaisesRegex(ValueError,"not expected"):v.validate(b)
 def test_segment(self):
  b=sample();struct.pack_into("<I",b,0x2c,0xFFFFFFFF)
  struct.pack_into("<H",b,0x15e,v.crc16(b[:0x15e]))
  with self.assertRaisesRegex(ValueError,"out of file"):v.validate(b)
if __name__=="__main__":unittest.main(verbosity=2)
