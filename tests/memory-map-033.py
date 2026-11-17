import unittest,importlib.util,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"windows/observer-033/memory_map.py"
s=importlib.util.spec_from_file_location("map033",p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
class Tests(unittest.TestCase):
    def setUp(self):self.s=m.Snapshot(bytes(0x400000),bytes([123])*0x4000,0x02ff0000)
    def test_main(self):self.assertEqual(self.s.read(0x3ffffc,4),bytes(4))
    def test_gap(self):self.assertIsNone(self.s.read(0x400000,1));self.assertIsNone(self.s.read(0x3fffff,2))
    def test_dtcm(self):self.assertEqual(self.s.read(0x1003ffc,4),b"{{{{");self.assertEqual(self.s.native_to_ra(0x02ff0004),0x1000004)
    def test_cross_dtcm(self):self.assertIsNone(self.s.read(0x1003fff,2))
    def test_no_arm7_mapping(self):self.assertIsNone(self.s.native_to_ra(0x03800000))
    def test_pointer(self):self.assertEqual(self.s.native_to_ra(0x02000100,4),0x100)
    def test_dsi(self):self.assertEqual(m.Snapshot(bytes(0x1000000),bytes(0x4000),0x02ff0000,True).read(0xffffff,1),b"\0")
    def test_bad_lengths(self):
        with self.assertRaises(ValueError):m.Snapshot(b"",bytes(0x4000),0x02ff0000)
if __name__=="__main__":unittest.main()
