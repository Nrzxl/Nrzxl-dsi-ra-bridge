# DSi RA Bridge 0.5.1 — ASMP EU PC per-frame event validation

STATUS: PC LAB QA ONLY / DRAFT. No official RetroAchievements awards.
Based on the actual 0.5.0 BizHawk observation in PR #9. The DSi XL
physical 0.4.4 baseline, SD, NAND, and original saves remain untouched.

## Improvements over 0.5.0
- Repeated HP damage and coin-associated recovery; dual health sources must
  agree within two frames. Only the 7 and 8 health levels may produce
  classifier events, since values lower than 7 were not confirmed.
- Lives hypothesis at ARM9 0x0209F2F4: all changes print a raw observation.
  A one-unit drop held for three subsequent frames, with unchanged numeric
  level and character, becomes LIVES_DROP_STABLE_CANDIDATE. This DOES NOT
  establish a death or validate the full meaning of the memory address.
  A death that immediately changes stage may only produce a raw observation.
- Character hypothesis at ARM9 0x0209CAE1: raw changes print, and a value
  held for three subsequent frames with stable stage becomes
  CHARACTER_VALUE_STABLE_CANDIDATE. Value 3 is NOT automatically Yoshi;
  the name must be checked against the visible game, and any character raw
  change clears the health baseline.
- Level ID 0x0209F2F8 is numeric only, NOT a confirmed named course.
  Reset on stage transition and allow 45 stable frames before re-arming.
- Detect any nonconsecutive BizHawk frame (rewind, repeated, skip) and
  reset baselines instead of inferring events from missing measurements.
- Observe LOADING_OR_UNVALIDATED_HP for values outside 7/8 or a mismatch
  older than two frames; never infer damage from the 8->16->0 transition.
- Preserve version 0.5.0 and its Lua script without replacement.

## At-home real BizHawk test

1. Open your legitimate own copy of Super Mario 64 DS Europe (ASMP) in
   BizHawk with melonDS. Use the same game setup that worked in 0.5.0.
2. Open Tools > Lua Console. STOP the older 049/050 Lua scripts first.
3. Open the new lab/bizhawk-asmp-eu-events-051.lua script.
4. Wait until the Lua Console logs ARMED level=... hp=8 in stable gameplay.
5. Take one controlled hit (8->7), collect a yellow coin (recovery 7->8),
   and repeat. Check for paired DAMAGE_OBSERVED and
   HEALTH_RECOVERY_COIN_CORRELATED, each once, no duplicates.
6. Observe the HUD lives count, deliberately lose a life in a controlled
   trial without risking existing saves, compare the raw lives candidate
   with the HUD. If a level loads immediately, only a RAW_CHANGE may show.
7. Change Yoshi to another playable character when possible. Compare
   the visible character with raw character candidate values. Do not
   label any number as a confirmed character name yet.
8. Enter and leave a stage. Confirm PHASE_TRANSITION_OBSERVED followed
   by ARMED after a stable period. HP 16/0 must never produce damage.
9. Send only text lines starting [DSIRB051] and written HUD observations.
   Do not share ROM, game saves, BIOS, passwords, RAM dumps or credentials.

## Experimental event labels (not official RA triggers)

DAMAGE_OBSERVED: supported 8->7, with paired health addresses.
HEALTH_RECOVERY_COIN_CORRELATED: 7->8 within 0–2 frames after coin increment.
HEALTH_RECOVERY_UNATTRIBUTED: 7->8 without coin in this time window.
COIN_UP_OBSERVED: one increment while the classifier is armed.
PHASE_TRANSITION_OBSERVED: raw numeric level changed.
LIVES_DROP_STABLE_CANDIDATE: raw lives decrement, 3-frame stable context.
CHARACTER_VALUE_STABLE_CANDIDATE: stable raw character value change.
GUARD FRAME_DISCONTINUITY: skipped or repeated frame; reset state.
GUARD HEALTH_PAIR_TIMEOUT: incompatible health values outlast the pairing
window; reset state without damage/recovery event.

These are only diagnostic labels. A cart header reading ASMP does not
attest the active ROM's RetroAchievements hash. No physical DSi is tested
by 051, no connection/account/login is used, and no awards are sent.

## Automated QA
Test the real Lua 051 script against synthetic 405-frame mock scenarios:
repeated hits, paired coin recovery, life decrease, two stable character
value changes, simultaneous level/lives transition, health 8->16->0, recovery
without coins, a mismatch exceeding two frames, frame discontinuity,
NLua proxy, binary and legacy memory readers, absent API, wrong cartridge
and wrong RAM size. Run 050/049 and 048–044 regressions on Linux and
PowerShell 5.1. Synthetic PASS is not physical or real-game validation.

The planned next milestone is controlled capture of specific memory values
every frame on the physical DSi XL ARM9; no 051 DSi build exists yet.
