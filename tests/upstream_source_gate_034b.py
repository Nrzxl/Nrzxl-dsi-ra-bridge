"""Pin audit ONLY: this is NOT a built nds-bootstrap fork or running retail monitor."""
import argparse
import json
from pathlib import Path

PINS = {
    "nds_bootstrap": "af351f096dd71a37e0e5b18d9709bcc0fb70342f",
    "dscheevos": "59e9978be7b9c3788357ef0a609caf9dc8ea74f3",
}


def require_text(root, relative, snippets):
    file = root / relative
    source = file.read_text(encoding="utf-8")
    missing = [piece for piece in snippets if piece not in source]
    if missing:
        raise AssertionError(str(file) + " missing hook contracts: " + str(missing))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=Path, required=True)
    parser.add_argument("--dscheevos", type=Path, required=True)
    args = parser.parse_args()
    require_text(args.bootstrap,
                 "retail/bootloaderi/source/arm7/dscheevos_hooks.c",
                 ["dscheevosWanted", "patchOsHalt", "dscheevosModuleCluster",
                  "DSCHEEVOS_S_PMK_VALID"])
    require_text(args.dscheevos,
                 "dscheevos/module/src/start.s",
                 ["vblank_entry", "halt_entry", "dscm_vblank_count", "module_shutdown"])
    print(json.dumps({
        "status": "SOURCE_CONTRACTS_FOUND",
        "pinned": PINS,
        "retail_loader_built": False,
        "hook_integrated_by_bridge": False,
        "physical_dsi_test": "NOT_RUN",
        "official_awards": 0,
    }))


if __name__ == "__main__":
    main()
