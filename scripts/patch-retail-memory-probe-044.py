#!/usr/bin/env python3
"""044: fail-closed read-only Mario main-RAM sampler in an isolated GPL checkout.

Run AFTER patch-offline-retail-043.py --apply, never on installed SD files.
This script edits a disposable, *pinned* source checkout, not an owner's game.
No ROMs, credentials, network, awards, NAND, ARM7 audio changes, or save writes.
The existing module/menu ABI changes from 7 to 8: mismatched binaries fail.
Modified DScheevos/nds-bootstrap sources remain GPL-3.0.
"""
import argparse
import json
import subprocess
from pathlib import Path

DSC = "59e9978be7b9c3788357ef0a609caf9dc8ea74f3"
BOOT = "af351f096dd71a37e0e5b18d9709bcc0fb70342f"
RC = "754965ef28db22b0411bfccbde39154cd09e6b79"
MARK = "HANNA_044_RAM_PROBE"
MAGIC = "0x34343044u"  # a marker, NOT an RA award
PREFIX_043 = "sd:/DSiRABridge_043/"
PREFIX_044 = "sd:/DSiRABridge_044/"

FIELDS = """  volatile uint32_t qa044_probe_magic;
  volatile uint32_t qa044_sample_frame;
  volatile uint32_t qa044_samples;
  volatile uint32_t qa044_digest;
  volatile uint32_t qa044_changed_windows;
  volatile uint32_t qa044_change_events;
  volatile uint32_t qa044_read_errors;
  volatile uint32_t qa044_bytes_per_sample;
"""

def revision(path):
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()

def replace_once(src, needle, replacement, label):
    count = src.count(needle)
    if count != 1:
        raise ValueError("044 upstream drift at %s: expected one anchor, got %d" % (label, count))
    return src.replace(needle, replacement, 1)

def plan(repo):
    repo = Path(repo)
    boot = repo / "external/nds-bootstrap"
    rc = repo / "external/rcheevos"
    if (revision(repo), revision(boot), revision(rc)) != (DSC, BOOT, RC):
        raise ValueError("044 requires exact pinned DScheevos/nds-bootstrap/rcheevos checkouts")
    files = {}
    session = boot / "retail/arm9/source/dscheevos_session.c"
    conf = boot / "retail/arm9/source/conf_sd.cpp"
    for path in (session, conf):
        s = path.read_text(encoding="utf-8")
        if "HANNA 043 OFFLINE" not in s and PREFIX_043 not in s:
            raise ValueError("044 requires prior 043 patch: " + str(path))
        files[path] = replace_once(s, PREFIX_043, PREFIX_044, str(path))

    # The executable header is written in assembly, not from the C macro.
    start = repo / "dscheevos/module/src/start.s"
    s = start.read_text(encoding="utf-8")
    s = replace_once(s, "\t.word 7                     @ DSCM_VERSION (the module test checks it matches)",
                     "\t.word 8                     @ DSCM_VERSION (044 ABI8 status)", str(start))
    files[start] = s

    hmod = repo / "dscheevos/module/include/dscheevos_module.h"
    s = hmod.read_text(encoding="utf-8")
    s = replace_once(s, "#define DSCM_VERSION 7u", "#define DSCM_VERSION 8u", str(hmod))
    s = replace_once(s, "  volatile uint32_t clock;            /* DSCM_CLOCK_*: the session's speed-ups (appended) */\n",
        "  volatile uint32_t clock;            /* DSCM_CLOCK_*: the session's speed-ups (appended) */\n" + FIELDS, str(hmod))
    files[hmod] = s

    hh = boot / "retail/common/include/dscheevos_hooks.h"
    s = hh.read_text(encoding="utf-8")
    s = replace_once(s, "#define DSCHEEVOS_VERSION         7",
                     "#define DSCHEEVOS_VERSION         8", str(hh))
    mirror = """\t// 043 module's existing appended status fields, mirrored for 044 ABI 8.
\tu32 captures;
\tu32 capturesStopped;
\tu32 framesStale;
\tu32 haltsIdle;
\tu32 haltsOther;
\tu32 aliasCached;
\tu32 clock;
""" + FIELDS.replace("  volatile uint32_t ", "\tu32 ")
    s = replace_once(s, "\tu32 idleCut; // idle passes a VBlank preempted\n",
        "\tu32 idleCut; // idle passes a VBlank preempted\n" + mirror, str(hh))
    files[hh] = s

    module = repo / "dscheevos/module/src/module.c"
    s = module.read_text(encoding="utf-8")
    if "HANNA 043 OFFLINE SPECTATOR ONLY" not in s:
        raise ValueError("044 needs 043 offline enforcement in ARM9 module")
    probe = """
/* HANNA_044_RAM_PROBE: bounded read-only NTR main-RAM observation.
 * 64 windows x 16 bytes (one per 64 KiB, offset +0x800), every >=120 frames.
 * Compares independent windows across samples. A changing digest is evidence
 * of dynamic RAM, NOT proof of a specific Mario variable/achievement.
 * Sampling is idle-only, spectator-only and cannot write game RAM. */
static uint32_t qa044_previous[64];
static uint32_t qa044_last_frame;
static uint8_t qa044_have_previous;
static void qa044_scan(void)
{
  uint32_t frame = g_frames, digest = 2166136261u;
  uint32_t changed = 0, i, j;
  uint8_t bytes[16];
  if (!(g_boot.flags & DSCM_BOOT_SPECTATOR) || g_boot.net_valid ||
      !dscm_g_status.active || frame - qa044_last_frame < 120u)
    return;
  qa044_last_frame = frame;
  for (i = 0; i < 64u; ++i) {
    uint32_t word = 2166136261u;
    const uint32_t addr = i * 0x10000u + 0x800u;
    if (read_memory(addr, bytes, sizeof(bytes)) != sizeof(bytes)) {
      dscm_g_status.qa044_read_errors++;
      return; /* fail closed: no false full sample */
    }
    for (j = 0; j < sizeof(bytes); ++j)
      word = (word ^ bytes[j]) * 16777619u;
    if (qa044_have_previous && word != qa044_previous[i])
      ++changed;
    qa044_previous[i] = word;
    digest = (digest ^ word) * 16777619u;
  }
  qa044_have_previous = 1;
  dscm_g_status.qa044_probe_magic = 0x34343044u;
  dscm_g_status.qa044_sample_frame = frame;
  dscm_g_status.qa044_digest = digest;
  dscm_g_status.qa044_changed_windows = changed;
  dscm_g_status.qa044_samples++;
  if (changed)
    dscm_g_status.qa044_change_events++;
  dscm_g_status.qa044_bytes_per_sample = 1024u;
}
"""
    s = replace_once(s, "static void publish_stats(void)\n",
                     probe + "\nstatic void publish_stats(void)\n", str(module))
    s = replace_once(s, "  dscm_g_status.halts_other = H.halts_other;\n",
                     "  dscm_g_status.halts_other = H.halts_other;\n  qa044_scan();\n", str(module))
    files[module] = s

    menu = boot / "retail/cardenginei/arm9_igm/source/dscheevosMenu.c"
    s = menu.read_text(encoding="utf-8")
    probe_menu = """
/* 044: display data ALREADY captured in idle time. No game RAM reads here.
 * The in-game menu can perturb audio; this page does no IRQ/FIFO work. */
static void drawQa044(const DScheevosStatus* s) {
    printCenter(16, 0, (const unsigned char*)"QA 044 - LIVE RAM", FONT_WHITE, false);
    print(1, 2, (const unsigned char*)"OFFLINE / READ ONLY", FONT_LIGHT_BLUE, false);
    if (s->qa044_probe_magic != 0x34343044u || !s->qa044_samples) {
        print(1, 5, (const unsigned char*)"No RAM sample yet", FONT_RED, false);
        print(1, 7, (const unsigned char*)"Run the game first", FONT_LIGHT_GRAY, false);
    } else {
        print(1, 4, (const unsigned char*)"Frame sampled", FONT_LIGHT_GRAY, false);
        printNum(18, 4, s->qa044_sample_frame, FONT_WHITE);
        print(1, 6, (const unsigned char*)"Samples", FONT_LIGHT_GRAY, false);
        printNum(18, 6, s->qa044_samples, FONT_WHITE);
        print(1, 8, (const unsigned char*)"RAM digest", FONT_LIGHT_GRAY, false);
        printNum(18, 8, s->qa044_digest, FONT_WHITE);
        print(1, 10, (const unsigned char*)"Windows changed", FONT_LIGHT_GRAY, false);
        printNum(18, 10, s->qa044_changed_windows, FONT_WHITE);
        print(1, 12, (const unsigned char*)"Change intervals", FONT_LIGHT_GRAY, false);
        printNum(18, 12, s->qa044_change_events, FONT_WHITE);
        print(1, 14, (const unsigned char*)"Read errors", FONT_LIGHT_GRAY, false);
        printNum(18, 14, s->qa044_read_errors, FONT_WHITE);
        print(1, 16, (const unsigned char*)"Bytes per sample", FONT_LIGHT_GRAY, false);
        printNum(18, 16, s->qa044_bytes_per_sample, FONT_WHITE);
    }
    print(1, 19, (const unsigned char*)"Not official RA awards", FONT_DARKER_GRAY, false);
    print(1, 22, (const unsigned char*)"RIGHT: Main B: Main", FONT_LIGHT_GRAY, false);
}
"""
    s = replace_once(s, "void dscheevosMenu(void) {\n", probe_menu + "\nvoid dscheevosMenu(void) {\n", str(menu))
    s = replace_once(s, "\tbool list = false;   // false: the summary page\n",
                     "\tbool list = false;   // false: the summary page\n\tbool probe044 = false;\n", str(menu))
    s = replace_once(s,
        "\t\t} else if (list) {\n\t\t\tdrawList(s, l, sel);\n",
        "\t\t} else if (probe044) {\n\t\t\tdrawQa044(s);\n\t\t} else if (list) {\n\t\t\tdrawList(s, l, sel);\n", str(menu))
    s = replace_once(s,
        "\t\t\tif (detail) {\n\t\t\t\tdetail = false;\n\t\t\t\tcontinue;\n\t\t\t}\n\t\t\tbreak;\n",
        "\t\t\tif (detail) {\n\t\t\t\tdetail = false;\n\t\t\t\tcontinue;\n\t\t\t}\n"
        "\t\t\tif (probe044) { probe044 = false; continue; }\n\t\t\tbreak;\n", str(menu))
    s = replace_once(s,
        "\t\tif (!list) {\n\t\t\tif (key & (KEY_RIGHT | KEY_DOWN)) {\n\t\t\t\tlist = true;\n\t\t\t}\n\t\t\tcontinue;\n\t\t}\n",
        "\t\tif (!list) {\n\t\t\tif (probe044) {\n\t\t\t\tif (key & KEY_RIGHT) probe044 = false;\n"
        "\t\t\t} else if (key & KEY_LEFT) {\n\t\t\t\tprobe044 = true;\n"
        "\t\t\t} else if (key & (KEY_RIGHT | KEY_DOWN)) {\n\t\t\t\tlist = true;\n"
        "\t\t\t}\n\t\t\tcontinue;\n\t\t}\n", str(menu))
    s = replace_once(s,
        '"RIGHT: List  B: Back"',
        '"LEFT: RAM RIGHT: List B: Back"', str(menu))
    files[menu] = s
    return files

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    files = plan(args.checkout)
    if args.apply:
        for path, body in files.items():
            path.write_text(body, encoding="utf-8")
    print(json.dumps({
        "status": "044_PATCHED_GPL_QA" if args.apply else "044_PATCH_PLAN_VALID",
        "paths": [str(p.relative_to(args.checkout)) for p in files],
        "sd_prefix": PREFIX_044,
        "module_abi": 8,
        "network": False,
        "spectator_only": True,
        "official_awards": False,
        "game_ram_reads": "64x16B @ +0x800 per 64KiB, 120-frame interval",
        "hardware": "NOT_RUN"
    }, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}))
        raise SystemExit(1)
