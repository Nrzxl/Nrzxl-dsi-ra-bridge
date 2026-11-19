#!/usr/bin/env python3
"""034D diagnostic, manually gated pinned DScheevos launcher main.

Replace upstream startup with explicit UI, FAT, config, ROM, chainload phases.
No automatic network/login/session/award calls. Never patches a retail ROM.
Fails closed if upstream main() layout changes.
"""
import argparse
import json
from pathlib import Path

# Bounded to a pinned upstream source tree; no executable source until QA build.
START = "int main(int argc, char** argv)\n{"
INJECT = r'''
/* DSIRB 034D diagnostic. A enters next phase, START holds for power-off. */
static void dsirb_gate(const char* stage) {
  ui_clear_bottom();
  ui_bottom("\nDSIRB 034D -- %s\n\nA   Continue\nSTART  Stop safely\n",
            stage);
  for (;;) {
    swiWaitForVBlank();
    scanKeys();
    int pressed = keysDown();
    if (pressed & KEY_START) {
      ui_status("Stopped. Power off.");
      for (;;) swiWaitForVBlank();
    }
    if (pressed & KEY_A) return;
  }
}
static void dsirb_block(const char* label) {
  ui_status("BLOCKED at %s. Power off.", label);
  for (;;) swiWaitForVBlank();
}

int main(int argc, char** argv) {
  (void)argc; (void)argv;
  int dsi_mode = 0;
  ui_init();
  ui_header("DSIRB 034D", "S0 UI OK");
  ui_status("S0: launcher main reached");
  ui_status("No RA, no login, offline");
  dsirb_gate("S0 screen");

  ui_status("S1: mounting internal SD...");
  if (!fatInitDefault()) dsirb_block("S1 SD");
  log_start();
  log_line("S1 SD mounted, log opened");
  ui_status("S1: sd:/ mounted");
  dsirb_gate("S1 SD");

  settings_load(&settings);
  settings.enabled = 0;
  settings.hardcore = 0;
  settings.live = 0;
  settings.spectator = 1;
  settings.username[0] = 0;
  settings.token[0] = 0;
  ui_status("S2: offline settings forced");
  log_line("S2 offline mode forced");
  if (!bootstrap_ini_game(rom_path, sizeof(rom_path), &dsi_mode)) {
    dsirb_block("S2 isolated INI");
  }
  ui_status("S2: isolated config OK");
  dsirb_gate("S2 INI");

  FILE* f = fopen(rom_path, "rb");
  if (!f) dsirb_block("S3 ROM open");
  unsigned char header[0x200];
  int valid = fread(header, 1, sizeof(header), f) == sizeof(header);
  fclose(f);
  if (!valid || header[0x12] != 0) dsirb_block("S3 NTR header");
  ui_status("S3: NTR ROM opens");
  log_line("S3 original NTR header readable");
  dsirb_gate("S3 ROM");

  ui_status("S4: ready to chainload");
  ui_status("Next A starts game; may fail");
  log_line("S4 ready for chainload; no network");
  dsirb_gate("S4 BOOT");

  log_line("S5 chainload requested");
  ui_status("S5: entering isolated bootstrap...");
  boot_game(0); /* no RA session/awards or network */
  dsirb_block("S5 returned");
}
'''

def apply(tree):
    main = tree / "dscheevos/launcher/source/main.c"
    source = main.read_text(encoding="utf-8")
    if source.count(START) != 1:
        raise ValueError("pinned main() entry not matched")
    if 'void boot_game(int with_achievements)' not in source:
        raise ValueError("missing original chainload helper")
    if "#define BOOTSTRAP_PATH DSC_DIR" not in source:
        raise ValueError("isolated bootstrap path missing")
    pre, old_main = source.split(START, 1)
    if "  ui_init();" not in old_main or "  log_start();" not in old_main:
        raise ValueError("upstream main layout changed")
    if "sd:/_nds/nds-bootstrap.ini" in pre:
        raise ValueError("legacy path remains in pre-main code")
    new = pre + INJECT
    if new.count("int main(int argc, char** argv)") != 1:
        raise ValueError("duplicate main")
    main.write_text(new, encoding="utf-8")
    return {"status": "034D_PINNED_STAGE_MAIN_PATCHED",
            "network_gates": "disabled_at_entry",
            "stage_count": 5,
            "retail_on_dsi": "NOT_RUN",
            "official_awards": 0}

def verify(tree):
    main = tree / "dscheevos/launcher/source/main.c"
    data = main.read_text(encoding="utf-8")
    for label in ("S0: launcher main reached", "S1: sd:/ mounted",
                  "S2: isolated config OK", "S3: NTR ROM opens",
                  "S4: ready to chainload", "S5 chainload requested",
                  "settings.enabled = 0;", "boot_game(0);"):
        if label not in data:
            raise ValueError("missing diagnostic gate: " + label)
    idx = data.index("int main(int argc, char** argv)")
    part = data[idx:]
    for forbidden in ("session_login(", "session_start(", "net_connect(",
                      "settings_menu(", "boot_game(1);"):
        if forbidden in part:
            raise ValueError("online/unsafe action in active main: " + forbidden)
    if part.index('dsirb_gate("S4 BOOT")') > part.index("boot_game(0);"):
        raise ValueError("boot is not behind explicit A gate")
    return {"status": "034D_MAIN_GATES_VERIFIED", "automatic_boot": False,
            "network_used": False, "official_awards": 0}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--mode", choices=("apply", "verify"), required=True)
    a = p.parse_args()
    try:
        report = apply(a.source) if a.mode == "apply" else verify(a.source)
        report.update(verify(a.source))
        print(json.dumps(report, sort_keys=True))
    except (OSError, ValueError) as e:
        print(json.dumps({"status":"BLOCKED", "reason":str(e)}))
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
