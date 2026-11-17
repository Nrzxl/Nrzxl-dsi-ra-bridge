# Repository checkpoint — 2026-11-16

- GitHub owner/repository: `Nrzxl/Nrzxl-dsi-ra-bridge` (PUBLIC; manually created by user).
- Default branch `main` includes the manual ARM diagnostic workflow, to make workflow_dispatch available.
- Experimental source branch: `feat/dsi-ra-bridge-diagnostic-build-020`.
- 42 source files recovered from the user-provided PowerShell initializer; this status file is additional.
- Local Node test results during recovery: protocol 632 PASS, client 7 PASS, synthetic NDS header 25 PASS.
- Docker/ARM compilation: NOT_RUN; DSi physical: NOT_RUN; live RetroAchievements: NOT_RUN.
- No console dumps, credentials, private keys, game ROMs or saves are intended for this repository.
- Do not install or replace `boot.nds`, `private/`, firmware, the R4 kernel, or Unlaunch.

## Manual build
Open GitHub Actions → ARM diagnostic manual 020 → Run workflow, choose the experimental branch and default image `devkitpro/devkitarm:20241104`. Inspect uploaded logs before attempting to use any generated `.nds`.

No automated deployment or Release is configured.
