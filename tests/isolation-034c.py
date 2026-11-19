"""034C offline packaging/isolation contract tests; never uses a retail ROM."""
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

isolate = load("iso_034c", "scripts/isolate-dscheevos-034c.py")
pack = load("pack_034c", "scripts/package-isolated-034c.py")

class IsolatedGate(unittest.TestCase):
    def test_new_names_do_not_overlap_old_paths(self):
        self.assertTrue(all("_nds/nds-bootstrap/" not in v and
                            "_nds/dscheevos/" not in v for _, v in isolate.REPLACEMENTS))
        self.assertEqual(len(isolate.UPSTREAM_REF), 40)
        self.assertEqual(len(isolate.BOOT_REF), 40)

    def test_offline_boot_defaults_and_blank_auth(self):
        self.assertIn("ENABLED = 0", pack.SETTINGS)
        self.assertIn("HARDCORE = 0", pack.SETTINGS)
        self.assertIn("SEND_DURING_PLAY = 0", pack.SETTINGS)
        self.assertIn("SPECTATOR = 1", pack.SETTINGS)
        self.assertIn("TOKEN =\n", pack.SETTINGS)
        self.assertIn("DSI_MODE = 0", pack.INI)

    def test_isolated_game_and_save_paths(self):
        self.assertIn("NDS_PATH = sd:/DSiRABridge_034C/games/selected.nds", pack.INI)
        self.assertIn("SAV_PATH = sd:/DSiRABridge_034C/saves/selected.sav", pack.INI)
        self.assertNotIn("_nds/nds-bootstrap.ini", pack.INI)
        self.assertNotIn("_nds/nds-bootstrap-release.nds", pack.GUIDE)

    def test_package_rejects_legacy_path(self):
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(Path(temp) / "test.zip", "w") as archive:
                with self.assertRaisesRegex(ValueError, "stable files"):
                    pack.add(archive, "_nds/nds-bootstrap-release.nds", b"x")
                with self.assertRaisesRegex(ValueError, "stable files"):
                    pack.add(archive, "_nds/dscheevos/session.bin", b"x")
                with self.assertRaisesRegex(ValueError, "unsafe"):
                    pack.add(archive, "../boot.nds", b"x")

    def test_isolation_apply_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            launcher = root / "dscheevos/launcher/source"
            module = root / "dscheevos/module/src"
            boot = root / "external/nds-bootstrap/retail/arm9/source"
            for folder in (launcher, module, boot):
                folder.mkdir(parents=True)
            (launcher / "config.c").write_text(
                's->enabled = 1;\ns->hardcore = 1;\ns->live = 1;\n'
                'strcpy(s->host, DEFAULT_HOST);\n'
                'read_ini("sd:/_nds/nds-bootstrap.ini", on_bootstrap, &g);\n'
                'read_ini("sd:/_nds/nds-bootstrap.ini", on_donor20, &g);\n'
            )
            (launcher / "config.h").write_text(
                '#define DSC_DIR "sd:/_nds/dscheevos/"\n'
            )
            (module / "module.c").write_text(
                '"sd:/_nds/dscheevos/session.bin"\n'
            )
            (boot / "main.cpp").write_text(
                '"sd:/_nds/nds-bootstrap/patchOffsetCache/"\n'
            )
            changed = isolate.patch(root)
            self.assertGreaterEqual(len(changed), 3)
            result = isolate.verify(root)
            self.assertEqual(result["status"], "PINNED_SOURCE_PATH_GATES_PASS")
            self.assertIn("s->enabled = 0;", (launcher / "config.c").read_text())
            self.assertIn("s->spectator = 1;", (launcher / "config.c").read_text())
            self.assertIn("sd:/_nds/dsirb034c/nds-bootstrap.ini",
                          (launcher / "config.c").read_text())

if __name__ == "__main__":
    unittest.main(verbosity=2)
