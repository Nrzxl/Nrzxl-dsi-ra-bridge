# DSi RA Bridge 0.5.2 - ASMP EU one-pass observer on PC

STATUS: EXPERIMENTAL PC ONLY / DRAFT QA. No official RA conditions,
login, awards, network or physical DSi changes.

## Public sources, technical scope and confidence

- EU lives, health and level: Skelux Hack64 documentation
  https://hack64.net/wiki/doku.php?id=super_mario_64_ds:skelux_documentation_eu
  and actual 0.5.1 game logs confirmed by user (PR #10).
- Europe ASMP star-completion bitmap 0x0209CAB4 to 0x0209CAC2 is
  supported by published EU legacy cheat addresses (not executed)
  and Kuribo64 discussion: one byte per course, 100-coin bit and
  seven regular stars. These are candidate save flags; increments
  are NOT equivalent to verified in-game star pickups.
  https://gamehacking.org/game/22856
  https://kuribo64.net/board/thread.php?id=324
- Saved best-coin records 0x0209CAD2..0x0209CAE0 from Europe
  Codejunkies address list. Do NOT confuse with live coins 0x0209F358.
- Cap save flag 0x0209CAA7 is mentioned by an EU never-lose-cap
  cheat. It is NOT proof a specific cap is currently worn.
- Europe player actor pointer 0x0209F394 from Kuribo64 discussion;
  in DS object documentation actor base+0x08 is a character/cap
  related byte. The old absolute US v1.0 pointer is NOT used.
  https://kuribo64.net/board/thread.php?pid=94175
  https://kuribo64.net/board/thread.php?id=333&page=27
  https://tasvideos.org/GameResources/DS/SuperMario64DS
- Red coin/silver star candidates: 0x0209F30C / 0x0209F310.
- Character/base candidate 0x0209CAE1 was observed to remain
  unchanged when the user wore Mario's cap in a prior PC run.
  This version compares it with actor base+0x08 before interpreting.

## One-pass observation design

Every emulator frame the Lua 052 reads a limited group of exact memory
locations, not the entire 4MiB RAM. It preserves all PC 051 event
guards (health 7/8, coins, phases, lives and base character).

Additional observations:
* STAR_FLAGS_RAW_CHANGE, STAR_FLAG_STABLE_GAIN_CANDIDATE and
  STAR_FLAGS_CHANGE_STABLE_CANDIDATE: 15-byte bitmap, require 3
  stable frames. Changes can be caused by loading different saves.
* COIN_RECORD_BYTE_CHANGE: candidate course coin records.
* CAP_SAVE_FLAG_RAW_CHANGE: unverified cap save/progression flag.
* ACTOR_CHAR_OR_CAP_RAW and CAP_OR_EFFECTIVE_CHARACTER_CANDIDATE:
  only when actor pointer is in 4MiB Main RAM, aligned and valid;
  require three stable frames with the same actor pointer and level.
  Never automatically label Yoshi/Mario/Luigi/Wario without visual QA.
* RED_COIN_CANDIDATE and SILVER_STAR_CANDIDATE: raw fields only.
* GAME_OVER_RESET_CANDIDATE: lives go from positive to 0, later
  HP reaches zero and lives reset from 0 to 3+ within 12000 frames.
  May also be save reload. Human visual confirmation REQUIRED.
* Compact SNAPSHOT every 900 frames for temporal/visual comparison.

Only the game memory is read-only: on Windows the script attempts
to create a plain text EVENT JOURNAL under the user's Downloads,
DSIRB052_<startframe>.txt, using a new available filename.
No ROM, save, BIOS, private RA patch, credentials or raw RAM dumps
are included. If the host journal cannot be created, read the
Lua Console as before.

## One single full gameplay to validate

1. Open your own Europe ASMP copy in BizHawk 2.11.1 melonDS.
2. Tools > Lua Console: stop 049/050/051, Open Script with
   lab/bizhawk-asmp-eu-observer-052.lua.
3. Confirm Reader selected, PC_JOURNAL ACTIVE or DISABLED, SNAPSHOT.
4. Play naturally: pick up two previously uncollected Power Stars;
   wear and remove Mario's cap; collect coins/red coins/silver stars
   if present; suffer damage/heal; lose lives and reach Game Over.
   Watch visible star count, cap appearance, HUD lives and note order.
5. Stop the script and send only DSIRB052 text from Downloads (or
   console) plus a brief list of what happened visually. Keep ROM,
   saves, firmware, BIOS, keys and RAM dumps on your own PC.

No guarantee of all 157 official achievement conditions. Mapping
their memory means auditing actual authorized trigger definitions,
including DTCM, pointers, stage overlays, timers, minigames, and
frame-perfect state. Do not claim official achievements or device
compatibility from this PC observer alone.

## CI

Lua 052 actual code tested against synthetic memory with 12 modes:
two star flags, no-star, cap changes, no-cap, invalid pointer,
Game Over reset, HP damage/recovery, lives, alternate memory APIs,
missing reader and wrong ROM/RAM. Legacy 051-044 regressions
on Linux/Windows. Synthetic CI does not equal real BizHawk test.
No merge, release, hardware DSi executable or award submission.
