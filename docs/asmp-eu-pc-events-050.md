# DSi RA Bridge 0.5.0 — ASMP/EU: PC event detector

STATUS: EXPERIMENTAL PC LAB ONLY / DRAFT QA. No DSi NDS, release or official achievements.
Based on 0.4.9 BizHawk real read-only monitor (PR #8). Physical DSi 0.4.4 remains unchanged.

## Procedure

1. Open your own Super Mario 64 DS ASMP Europe game in BizHawk melonDS (DS mode).
2. In Tools > Lua Console, **stop** the old 049 script first; do not run both.
3. Use Open Script with lab/bizhawk-asmp-eu-events-050.lua from the NEW 050 package.
4. The Lua Console prints the chosen reader, safety warning, an ARMED message
   after stable gameplay, and diagnostic EVENT lines.
5. Observe a controlled hit, a coin pickup, and a loading/level change. The
   overlay shows level, coins, lives, health, alternate health and guard state.
6. Share only the text lines beginning [DSIRB050], not any ROM, RAM dump, save,
   BIOS or user credentials. Stop the script to stop the monitor.

## What the 050 actually detects

The following event labels are observations, NOT official RA triggers:

- PHASE_TRANSITION_OBSERVED: numerical level ID changed. No assumption
  about which named stage was entered. Clears the health baseline and arms
  a 45-frame warmup gate.
- COIN_UP_OBSERVED: observed increment by exactly one at 0x0209F358
  while the detector is armed.
- DAMAGE_OBSERVED: both read-only health addresses reflect a matching
  one-unit reduction, with their raw updates at most TWO frames apart.
- HEALTH_RECOVERY_COIN_CORRELATED: a paired health rise by one, and a
  coin increment in the same frame or within the prior TWO frames.
  Coin association is temporal, not proof of causality.
- HEALTH_RECOVERY_UNATTRIBUTED: a paired rise by one with no recent coin.

Published PAL address references:
- Yellow coins: ARM9 0x0209F358 (Main RAM offset 0x09F358).
- Level ID: ARM9 0x0209F2F8.
- Primary health hypothesis: ARM9 0x0211117C.
- Alternate health hypothesis: ARM9 0x02092144.
- Lives, for overlay context only: ARM9 0x0209F2F4.

The user-provided real BizHawk evidence with Yoshi (character 3 by
human identification) showed damage 8->7 / 2176->1920, followed by
recovery 7->8 / 1920->2176 when collecting a coin.
Hypothesis (only corroborated for health 7 and 8):
alternate_health = primary_health * 256 + 128.
Lower health values and character-selection memory remain unverified.

## No false official awards

- All reads are FROM emulator RAM; no memory writes, savestates, network
  traffic, RA authentication, achievements, SD or NAND changes.
- ASMP cartridge header is checked, NOT active ROM RA hash. If no
  trustworthy ASMP header or compatible read-only API is available, the
  Lua script blocks rather than pretending an attestation.
- Initial, level-transition and health-invalid states reset the detector.
  Re-arming requires 45 coherent frames. Health value zero, >8, or an
  invalid alternate representation blocks event classification.
- Two mismatched health readings get a two-frame reconciliation window.
  Persistent mismatch and unpaired/multi-unit health changes disarm.
  This prevents interpreting 8->16->0 loading values as damage/healing.
- Official RetroAchievements definitions have not been imported or run.
  No awards are sent. No physical DSi gameplay has been tested by 050.

## Automated tests

The actual 050 Lua runs against synthetic mocked memory in multiple modes:
binary reader, NLua callable proxy, 0-indexed array, legacy readbyte,
coin-correlated recovery, uncorrelated recovery, update lag >2 frames,
missing read APIs, wrong cartridge code, level transition and health
8->16->0 loading. Linux also runs Python source gates and regressions
for 049, 048, 047, 046, 045 and 044; Windows runs Python regressions.
Tests DO NOT emulate actual Nintendo DS hardware or unlock achievements.

Sources:
https://hack64.net/wiki/doku.php?id=super_mario_64_ds:skelux_documentation_eu
https://sites.google.com/site/jamesskingdom/Home/video-game-secrets-by-james-s/super-mario-64-ds-exposed
https://tasvideos.org/Bizhawk/LuaFunctions
