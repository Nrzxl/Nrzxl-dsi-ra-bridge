# DSi RA Bridge 0.3.4-B: memory gate + removable scout

**Scope:** experimental pre-integration, NOT a retail monitor.
Branch: feat/dsi-ra-bridge-retail-scout-034b (derived from 034-A).
033 physical fixture evidence: https://github.com/Nrzxl/Nrzxl-dsi-ra-bridge/issues/1
Retail roadmap: https://github.com/Nrzxl/Nrzxl-dsi-ra-bridge/issues/2
032 PEER TIMEOUT: OPEN. Release, merge, OTA, NAND and firmware updates: NONE.

## 034B-1: Memory and overlay inspection (read-only)

Source: scripts/retail_memory_gate_034b.py. Inspects DS ARM9/ARM7 overlay tables
(from header 0x50 and 0x58), bounds-checks size and entries, parses RAM/BSS
footprints and checks declared sections for intersection with the tentative
DScheevos module window 0x02D80000–0x02F80000. No game files are changed.

To run from the existing Super Mario 64 DS folder on Windows PowerShell 5.1
with Python 3.10+ (the user has Python 3.12):
~~~powershell
New-Item -ItemType Directory -Force -Path ".\DSIRB_034B" | Out-Null
$base = "https://raw.githubusercontent.com/Nrzxl/Nrzxl-dsi-ra-bridge/feat/dsi-ra-bridge-retail-scout-034b/scripts"
Invoke-WebRequest "$base/retail_preflight_034.py" -UseBasicParsing -OutFile ".\DSIRB_034B\retail_preflight_034.py"
Invoke-WebRequest "$base/retail_memory_gate_034b.py" -UseBasicParsing -OutFile ".\DSIRB_034B\retail_memory_gate_034b.py"
python ".\DSIRB_034B\retail_memory_gate_034b.py" ".\Super Mario 64 DS (USA) (Rev 1).nds"
~~~

Result:
- BLOCKED_DECLARED_RESERVATION_OVERLAP: definite overlap of declared loads;
  exit 3. Do not patch or load with a hypothetical monitor.
- NO_DECLARED_OVERLAP_RUNTIME_UNPROVEN: no overlap declared in the inspected
  headers and overlay tables, but **NOT** a compatibility verdict. nds-bootstrap
  uses high RAM for its ROM cache; dynamic heap/BSS, actual overlays, SCFG,
  MPU/cache and runtime hooks still need investigation.
- BLOCKED: malformed or unreadable file, no ROM modification.

The script prints no ROM path or data and makes no network request or account
authentication.

## 034B-2: Isolated homebrew capability scout (NOT a retail game)

Sources: dsi/scout-034b/source/main.c, Makefile. A complete .nds intended
for existing Flipnote Lenny -> HBMenu, with normal ARM7 SDK code.
Build: deterministic two-pass pinned devkitARM, binary and header validation,
then optional zipped SD-only artifact. CI failure means NO physical use.

Reports only DSi mode, internal sd:/ mount, a 4096-byte **own** buffer checksum,
VBlank counter, heap symbols. No SCFG or MBK writes or probes, ROM/game
loads, NDA/NAND writes, R4, Wi-Fi, gameplay, external memory scan or awards.
Press X after 300 frames to save SCOUTnnn.txt exclusively to a new
sd:/DSiRABridge_034B folder, only if DSi mode + sd:/ confirmed.
No old reports are overwritten.

**Physical 034B: NOT_RUN.**
When the CI artifact exists and passes, back up the SD, extract its
DSi_RA_Bridge_034B_Scout_SD_ONLY.zip on a PC and copy ONLY the new
nds/DSiRABridge_034B folder. Launch from HBMenu using the already working
Flipnote Lenny path. If DSi mode or SD is NO, stop. Never change NAND,
Unlaunch, boot.nds, private/, TWiLight++ or older DSiRABridge folders.
Photograph the screen; optionally save SCOUTnnn.txt, then START and power off
before removing SD. Remove by deleting only new 034B folders. The ZIP
includes TESTE_034B.md with exact steps.

## Pinned GPL upstream source contracts (not built/deployed)

- DScheevos: skierrz/dscheevos at 59e9978be7b9c3788357ef0a609caf9dc8ea74f3 (GPL-3.0).
- nds-bootstrap: skierrz/nds-bootstrap at af351f096dd71a37e0e5b18d9709bcc0fb70342f (GPL-3.0).

CI fetches those exact sources for **source-only** verification that the
module's halt/VBlank entry symbols and the retail bootloader's OS_Halt/module
hook points exist. It does NOT compile a usable retail nds-bootstrap fork or
ship upstream proprietary/third-party dependencies; no GPL code is merged
into the original MIT observer. Future GPL development must keep all source,
license notices and complete corresponding build materials separate.

033 passed because B had already been instrumented before launch. A generic
launcher thread does not survive nds-bootloader memory and ARM7/IRQ reset.
Retail requires an integrated loader that reserves memory *before* the game
startup and reduces the bootstrap ROM cache. The 034B reserved window is a
candidate based on this pinned fork, NOT guaranteed free RAM. Real retail
support still requires evaluating ARM9/ARM7 cardengines, OS_Halt idle,
DTCM/CP15, dynamic pointer sets, snapshots with frame fidelity, save
integrity, sound, net stability and RetroAchievements client authorization.

## Gate matrix

| Gate | Status |
|---|---|
| 033 fixture observed on DSi XL | PASS |
| 034-A Super Mario 64 DS structural preflight | PASS (user log) |
| 034-B overlay/declared RAM scan | automated synthetic tests only |
| 034-B DSi physical capability scout | NOT_RUN pending CI and physical |
| 034-B pinned GPL upstream contracts | source-only automated gate |
| Retail loader with real game memory monitoring | NOT_IMPLEMENTED |
| Runtime rcheevos official session/unlocks | NOT_IMPLEMENTED |
| 032 PEER TIMEOUT physical | OPEN |

No ROMs, saves, NAND, OTP, console identifiers, credentials or OBS000.bin
are uploaded to GitHub by this branch or its CI.
