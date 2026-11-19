"""034D stage gates: synthetic source checks, no ROMs and no console.
Not a physical runtime compatibility test.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gate034d",
        ROOT / "scripts/patch-launch-stage-034d.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class StageGateTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.path = self.root / "dscheevos/launcher/source/main.c"
        self.path.parent.mkdir(parents=True)
        self.original = ('#define BOOTSTRAP_PATH DSC_DIR "nds-bootstrap.nds"\n'
                         'static void boot_game(int with_achievements) {}\n'
                         'int main(int argc, char** argv)\n'
                         '{\n'
                         '  ui_init();\n'
                         '  ui_header("", NULL);\n'
                         '  log_start();\n'
                         '  boot_game(0);\n'
                         '}\n')
        self.path.write_text(self.original)

    def test_every_stage_requires_confirmation(self):
        result = gate.apply(self.root)
        self.assertEqual(result["stage_count"], 5)
        data = self.path.read_text()
        gate.verify(self.root)
        self.assertLess(data.index('dsirb_gate("S0 screen")'), data.index("fatInitDefault()"))
        self.assertLess(data.index('dsirb_gate("S1 SD")'), data.index("settings_load(&settings)"))
        self.assertLess(data.index('dsirb_gate("S2 INI")'), data.index("fopen(rom_path"))
        self.assertLess(data.index('dsirb_gate("S4 BOOT")'), data.index("boot_game(0);"))
        self.assertIn("settings.token[0] = 0", data)
        self.assertIn("settings.enabled = 0", data)

    def test_fail_closed_when_main_layout_changed(self):
        self.path.write_text(self.original.replace("  log_start();", ""))
        with self.assertRaisesRegex(ValueError, "layout"):
            gate.apply(self.root)

    def test_fail_closed_when_legacy_path_present(self):
        self.path.write_text(self.original.replace("static void boot_game",
                              'const char *x="sd:/_nds/nds-bootstrap.ini";\nstatic void boot_game'))
        with self.assertRaisesRegex(ValueError, "legacy"):
            gate.apply(self.root)

    def test_never_allow_online_api_in_main(self):
        gate.apply(self.root)
        self.path.write_text(self.path.read_text() + "\nsession_start(x);\n")
        with self.assertRaisesRegex(ValueError, "online/unsafe"):
            gate.verify(self.root)

if __name__ == "__main__":
    unittest.main(verbosity=2)
