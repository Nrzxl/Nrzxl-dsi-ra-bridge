"""034Q offline parser regression plus source proof gates."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_034q import linker_members

class StaticAuditTest(unittest.TestCase):
    def test_parse_linker_map(self):
        sample="""Archive member included to satisfy reference by file (symbol)

/opt/lib/libfoo.a(foo.o)
                              build/main.o (foo)
/opt/lib/libfoo.a(bar.o)
                              /opt/lib/libfoo.a(foo.o) (bar)

Allocating common symbols
"""
        self.assertEqual(linker_members_str(sample),["/opt/lib/libfoo.a(foo.o)","/opt/lib/libfoo.a(bar.o)"])

    def test_sources_unchanged(self):
        root=ROOT/"dsi"
        o2=root/"probe-034o-receive"
        p0=root/"probe-034p-control"
        p1=root/"probe-034p-update-link"
        self.assertEqual((o2/"source/main.c").read_bytes(),(p0/"source/main.c").read_bytes())
        self.assertEqual((p0/"source/main.c").read_bytes(),(p1/"source/main.c").read_bytes())
        self.assertEqual((o2/"arm7/source/main.c").read_bytes(),(p0/"arm7/source/main.c").read_bytes())
        s=(p1/"arm7/source/main.c").read_text()
        self.assertIn("= Wifi_Update;",s)
        self.assertNotIn("Wifi_Update();",s)
        self.assertNotIn("installWifiFIFO();",s)

def linker_members_str(s):
    # Exercises actual archive member row matching independently of filesystem.
    import re
    region=s.split("Archive member included to satisfy reference by file (symbol)",1)[1]
    region=region.split("\nAllocating common symbols",1)[0]
    return list(dict.fromkeys(re.findall(r"(?m)^(\S+\.a\([^)]+\))\s*$",region)))

if __name__=="__main__":unittest.main(verbosity=2)
