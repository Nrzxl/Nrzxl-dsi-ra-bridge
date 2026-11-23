# DSi RA Bridge 0.4.4 — Mario ASMP live main-RAM read-only probe

## Scope / status

**044 is experimental, PHYSICAL NOT_RUN until new evidence.** The 043 retail loader and DScheevos in-game menu booted on a real DSi XL per user's report (19–23 Nov 2026); menu opening intermittently distorts audio, sometimes recovers after another menu cycle. Audio bug remains OPEN and is deliberately *not* changed in 044.

This candidate extends 043 and **does not change NAND, Unlaunch, Flipnote Lenny, main SD, ROM/save, Wi-Fi settings, credentials, or official awards**. Hard offline/spectator gates remain. Always use a separate *cloned* spare SD; 044 only writes/consumes experimental session and scratch files on that spare SD. No copy of Mario, firmware, saves, IDs or personal credentials belongs in GitHub.

## Actual new implementation

- `scripts/patch-retail-memory-probe-044.py` runs **after** the verified 043 source patcher on pinned *disposable* GPL source checkouts. It changes the experimental path to `sd:/DSiRABridge_044/`, extends status with exactly eight 32-bit counters and increments **module ABI 7 → 8**, matched in nds-bootstrap. No mix of 043/044 binaries.
- `dscheevos/module/src/module.c` already provides real DS main RAM reads (`0x02000000 + logical offset`) and conditional DTCM reads through its `read_memory` platform. 044 adds a diagnostic only for DS main RAM: **64 windows x 16 bytes, one every 64 KiB from logical +0x800** (1,024 bytes/sample), no more than **once per 120 frames**, called in the pre-existing idle/stats path when module is active, offline and spectator. It never writes to game RAM, never scans VRAM or firmware, and does not introduce interrupt/ARM7 audio work.
- The module publishes sample frame, count, 32-bit FNV-1a-based digest, number of windows changing versus preceding sample (0–64), intervals with changes, read errors, and bytes/sample to its private status. It is **not a screenshot, an RA condition, or a save/memory dump**. A digest changing across time is evidence that the probe sees changing RAM, **not attribution to any particular Mario variable**.
- `retail/cardenginei/arm9_igm/source/dscheevosMenu.c` adds a **LEFT → QA 044 - LIVE RAM** screen from the existing RetroAchievements summary. Right/B returns to summary. UI reads status only, **does not sample memory in the menu**, and introduces no new ROM hacking/online code. Existing `Frames checked` and `Frames skipped` stay on the original RA summary.
- `scripts/prepare-offline-game-044.py` creates a new Windows staging location and `DSiRABridge_044`, verifying the ASMP original against the user's 042 preflight and both 044 binaries against `build-manifest-044.json`. It demands ARM9 module ABI8, spectator/offline flags, dummy `LOCAL_QA` identity, no real token. The synthetic 300/900-frame conditions are explicitly **engine-only** tests and do not count as RAM proof or official unlocks.
- Sources: DScheevos `59e9978be7b9c3788357ef0a609caf9dc8ea74f3`, nds-bootstrap `af351f096dd71a37e0e5b18d9709bcc0fb70342f`, rcheevos `754965ef28db22b0411bfccbde39154cd09e6b79`. Corresponding GPL patches are packaged by the build.

## CI gates

Workflow `offline-game-observer-044.yml` must:
1. Verify pinned checkouts and apply 043 then 044 patches, fail closed on source drift.
2. Run 043 legacy + 044 unit tests, preflight 042, observer 041, and real DScheevos core suite.
3. Independently verify Python and real pinned rcheevos C hash on **synthetic NDS**.
4. Cross-compile ARM9 module ABI8 and retail nds-bootstrap with matched 044 status/RA menu; check module magic/ABI, NDS CRC/header, hashes.
5. Stage a synthetic 044 kit using the *actual compiled binaries*, with no commercial ROM in the artifact, and include all source patches.
6. Publish **PHYSICAL_NOT_RUN** artifact only after all gates succeed. No automated release or merge.

## Physical gate (ONLY after successful CI; spare SD)

Prepare new staging on Windows using the pre-existing ASMP ROM locally and original preflight report. The `--out` destination MUST be a new path under the Windows user profile. Copy only `SD_ROOT` contents to a cloned spare card with the Lenny/HBMenu environment, never the production card. First run may consume `session.bin` into `session.used`.

During a Mario session: observe game/controls, avoid unnecessary menu cycles because audio glitch is still open. Play for ~2–3 minutes, enter RetroAchievements menu once. On the **summary**, note `Frames checked`, `Frames skipped`; press **LEFT** once, note `RAM digest`, `Samples`, `Windows changed`, `Read errors`, `Frame sampled`. Return, play/perform a controlled action, revisit after ~2 minutes if stable. Do not interpret the digest as a known address/achievement. Stop if the game hangs, audio disappears or save behavior is abnormal; use original SD to roll back.

## Proof and next boundary

- **Static/CI pass** means binaries/source agreed; **PHYSICAL PASS** requires user-reported evidence on DSi and menu values.
- **LIVE_MAIN_RAM_PROBE PASS** requires *at least two* samples on DSi where `Samples` grows, `Frame sampled` advances, `Read errors=0` and `Windows changed>0` and/or digest changes; a single digest cannot prove dynamic reading.
- **Specific MARIO VARIABLE PROOF** remains pending until a validated address and an action-linked A/B experiment exist. DTCM is not scanned in 044.
- **Official RetroAchievements awards** remain disabled, with no RA login, network, cloud sync, fake award submission, or guarantee of syncing an offline session afterward.
- No automatic completion claims for 044 when only the 043 physical test exists.

Historical fixed target: `Super Mario 64 DS (Europe) ASMP`, official game 9983, DS hash `ba3c4052e00c5cc31df5d5534c39de1b`. This public RA content hash is not the ROM SHA256.
