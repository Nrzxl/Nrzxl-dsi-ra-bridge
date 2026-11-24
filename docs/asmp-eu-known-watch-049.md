# DSi RA Bridge 0.4.9 — known ASMP EU PC watch

STATUS: PC_LAB_QA_ONLY. No DSi package, no release or merge.
Based on existing 048 lab. DSi physical baseline 0.4.4 is preserved.
No NAND, Unlaunch, memory writes, cheats, savestates, RA unlocks or network.

## Sources
- PAL/UK memory map: https://sites.google.com/site/jamesskingdom/Home/video-game-secrets-by-james-s/super-mario-64-ds-exposed
- Skelux Europe: https://hack64.net/wiki/doku.php?id=super_mario_64_ds:skelux_documentation_eu
- Europe GameHacking coin code: https://gamehacking.org/game/22856
- Europe decompilation, for future symbol analysis: https://github.com/tangosdev/sm64ds-decomp

The authoritative structured listing with per-field evidence is at research/asmp-eu-known-addresses-049.json.
0x0209F358 yellow coins matches HUD 0->1, 3->4 and 4->5 in PC BizHawk reports.
Other addresses and widths are published hypotheses, NOT yet validated in emulator or DSi.
Original pages often say 8-bit? or 16-bit?; those widths remain provisional.
USA 1.0 addresses are not interchangeable. Do not promote unverified save-bit layouts.

## Live use with YOUR legally held ASMP EU ROM
1. Start EmuHawk, load game with melonDS DS core.
2. Tools > Lua Console > Open Script > lab/bizhawk-asmp-eu-live-watch-049.lua
3. The overlay reads only eight fields live. Lua Console prints only CHANGES.
4. Stop the script through Lua Console when finished.
5. Test one variable at a time with idle controls. Do not trust data when the ROM
   header cannot be read; the Lua aborts rather than pretending validation.
No files are written by the Lua monitor and no memory dumps are required.

## Offline 048 captures
Use scripts/inspect-asmp-known-049.py (3 before/idle/after BINs + metadata) or
scripts/Invoke-MarioKnown-049.ps1 in Windows PowerShell 5.1.
Reports contain only eight numbers per snapshot, no memory dumps.
Do not upload any .bin, ROM, save or key. A game-code header is not an RA hash.
Offline tools can check a local owned ROM but cannot prove it is the loaded ROM.
The PowerShell helper uses the latest completed AFTER and deterministic report
naming: it will not silently reanalyze an old session for the same event.

## Gates
- Python and Lua mocked unit tests plus 048-044 regression in Actions.
- Manual verification in real BizHawk remains required for non-coin fields.
- Physical ARM9 hardware QA requires separate authorized build; no DSi change.
- Official RA conditions + account/compliance authorization required before awards.

## BizHawk compatibility fix (049, November 24 2026)
- `memory.read_bytes_as_binary_string` was added in BizHawk 2.11 and may be missing.
- Earlier 049 used a static `type(memory.read_bytes_as_binary_string) == "function"`
  assertion, then relied exclusively on binary read. This caused the user's
  real NLua error even after the previous fix.
- The monitor now probes **actual read results** and picks the first working
  read-only API: binary string, 1-/0-indexed byte array, `read_u8`, `readbyte`.
  No static function-type test is used. All widths are decoded as unsigned
  little-endian values. It logs the selected reader to the Lua Console.
- If none work, no monitoring starts (fail closed); if ASMP ROM header is
  unavailable, it refuses to run. This does not verify a RetroAchievements hash.
- GitHub Actions exercises the **actual Lua monitor** with each mock API mode,
  including callable proxy (non-"function"), broken binary, missing APIs, and
  wrong cartridge code. Real BizHawk validation is separate.
- Stop/remove any old running Lua script in Tools > Lua Console before opening
  the fresh package's script. Do not reuse older Actions artifact ZIPs.
- Official documentation: https://tasvideos.org/Bizhawk/LuaFunctions
  and upstream release history: https://github.com/TASEmulators/BizHawk/issues/3035 .
