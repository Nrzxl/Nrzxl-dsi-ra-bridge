# DSi RA Bridge — 0.4.5 RA set-wide coverage: Mario 64 DS

**Status: HOST CATALOG/STATIC QA ONLY. Not a new DSi installer; PHYSICAL 045 NOT_RUN.** This phase prepares exhaustive *inventory*, NOT an automatic guarantee of all achievements. Existing 0.4.4 is the latest physical RAM observer PASS (two user photos); existing 0.4.3 is boot/menu rollback; audio menu glitches remain OPEN. Do not alter stable SD or NAND.

## Authoritative input and important limitations

- Official game: [Super Mario 64 DS (Nintendo DS), game ID 9983](https://retroachievements.org/game/9983). The base set displayed **157 achievements** when researched 23 Nov 2026. This count may change following set revisions. EU ASMP RA content hash: `ba3c4052e00c5cc31df5d5534c39de1b`. This is NOT the user ROM SHA256.
- The [GetGameExtended v1](https://api-docs.retroachievements.org/v1/get-game-extended.html) API returns metadata, IDs, names, descriptions, points and `MemAddr` as **MD5 of the achievement logic, NOT the logic itself**. **Never mistake that digest for a memory address/trigger.** The API needs a *web API key*; no key is in GitHub and the script reads it only from `RA_WEB_API_KEY` on the user's PC.
- Exact game predicates require an **already authorized local raw game patch** plus the actual `rcheevos` runtime. The optional `--authorized-patch` input must stay on the user's PC. It contains authored trigger text and might contain account identifiers. Do not share it or commit it. The script only extracts syntactic references, not pointer values nor achievement evaluations.
- `rcheevos` supports temporal logic (Delta/Prior, hit counts, PauseIf/ResetIf, measured conditions, addresses calculated from pointers, alternate groups, time/count flags). A regex scan of trigger strings **cannot validate any of that**. The only acceptable final evaluator is the original `rcheevos` set running against true game snapshots.
- Official awards, sessions, leaderboards and credentials stay **disabled** in our DSi QA until we obtain the correct approved client/security pathway. No claims of retroactive synchronization.

## Completed in branch QA 045

`scripts/ra-set-coverage-045.py` generates a **sanitized per-achievement catalog**:

1. Accept local official `GetGameExtended` response JSON, or retrieve once using the locally configured `RA_WEB_API_KEY` over HTTPS (no key/token emitted in output).
2. Validate expected game ID, achievement IDs, nonempty titles/descriptions and logic digests; reject duplicates, malformed input, oversize inputs, incorrect game.
3. Classify descriptions into nonexclusive research topics: stars; coins; lives/health/damage; time/speed; stages/bosses; characters; minigames; scores/leaderboards; progression/flags; restrictions (no-damage, no caps, etc.). A keyword category is **not** proof of which memory addresses a predicate uses. Unclassified entries remain explicitly unclassified.
4. Compute a SHA256 fingerprint over the canonical metadata: when RA modifies a set, a new snapshot detects drift instead of reusing obsolete address assertions.
5. With optional already-authorized local game patch, index plain numeric `0x` address references and note whether they fall within DS main RAM (`0x000000..0x3fffff`), DTCM logical RA (`0x1000000..0x1003fff`) or unsupported/unmapped. Report missing/extra achievements without assigning them physical addresses or simulating evaluation.
6. Hardcode all physical/official award flags as **FALSE**; report remains `OFFICIAL_METADATA_INDEXED_RAW_TRIGGERS_PENDING` or `TRIGGER_ADDRESSES_INDEXED_NOT_EVALUATED`. Never put raw patch, key, ROM, save, or RAM dump into output.
7. CI uses only fabricated metadata/conditions and verifies **no data is sent online**.

### Fluxo assistido para Windows 11 / PowerShell 5.1 (recomendado)

A chave fica **somente no processo local** e é introduzida em um campo oculto. A consulta GET sobre HTTPS é enviada **apenas ao domínio oficial retroachievements.org**; nenhuma chave é escrita no projeto, no relatório, no histórico do PowerShell ou nas Actions. Não enviar a chave por chat.

1. Acesse https://retroachievements.org/controlpanel.php após login → **Keys** → **Web API Key**.
2. No [PR #4](https://github.com/Nrzxl/Nrzxl-dsi-ra-bridge/pull/4), abra a branch `qa/dsi-ra-coverage-045-20261123`, clique em **Code > Download ZIP** e extraia a pasta completa em Downloads.
3. No Explorador, abra a pasta **raiz** extraída (que contém `scripts`); digite `powershell` na barra de endereço e Enter.
4. Execute este comando **sem inserir nenhuma chave na linha de comando**:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\iniciar-catalogo-ra-045.ps1
```

5. Quando o console solicitar `Web API Key (entrada oculta)`, cole a chave. O PowerShell não exibirá os caracteres. O script remove a variável temporária ao encerrar, inclusive quando ocorre erro.
6. Resultado esperado: `CATALOGO_045_IMPORTADO_COM_SUCESSO`, total de conquistas e caminho do arquivo **`RA_9983_coverage_045_AAAAMMDD_HHMMSS.json`** em Downloads. O total vem da resposta oficial, **não é fixado em 157**.
7. Se quiser revisão no ChatGPT, **envie somente esse JSON de cobertura gerado**; não envie a chave, o JSON bruto da API, ROM, arquivos de save ou patch autenticado.

O assistente também aceita `-MetadataFile` apontando para um JSON legítimo já salvo localmente, para trabalhar **sem rede**. No CI Windows o mesmo caminho é testado somente com arquivo sintético.

**Este passo não instala nada no DSi.** Mantemos a 0.4.4 no SD reserva, e a 0.4.3 de rollback. O catálogo importado não contém o corpo das condições RA; a etapa seguinte requer uso autorizado de definições completas e `rcheevos` por frame.

### Local use on Windows / PowerShell 5.1

If you already have an **official GetGameExtended JSON export** for game 9983:

```powershell
py -3 .\scripts\ra-set-coverage-045.py `
  --game-extended "$env:USERPROFILE\Downloads\RA_9983_extended_local.json" `
  --out "$env:USERPROFILE\Downloads\RA_9983_coverage_045.json"
```

Or, **only on your own PC**, if you have your RetroAchievements Web API key, set `RA_WEB_API_KEY` as a temporary environment variable **without committing or sending the key**. Then run:

```powershell
py -3 .\scripts\ra-set-coverage-045.py `
  --fetch-ra-api `
  --out "$env:USERPROFILE\Downloads\RA_9983_coverage_045.json"
Remove-Item Env:\RA_WEB_API_KEY -ErrorAction SilentlyContinue
```

No key is required for the tests or for the previously validated DSi 0.4.4. A raw game patch (if independently obtained via a legitimate client) may be supplied with `--authorized-patch <local_file>`; **never upload that file or put API credentials into commands/history or GitHub**. This script does not fetch raw authenticated client game patches, impersonate a device or transmit awards.

## Large-scale test matrix (RA categories versus real 60Hz data)

| Class | Example QA event | What needs to be verified |
| --- | --- | --- |
| Stars | acquire one Power Star; course/total progress | permanent star flags vs total; no false positives on load |
| Coins | pick one coin, 100-coin star, red/silver coin | per-stage counts vs totals; reset when leaving stage |
| Lives / damage | lose life, take damage, restore health | 8/16/32-bit widths; distinguish HP from lives and no-hit runs |
| Time / speed | enter timed race, countdown, finish | game timer vs wall time vs frame clock; time paused in menu; required precision |
| Course/character | warp, enter course, swap Mario/Yoshi/Luigi/Wario | stable stage IDs, flags and pointer chains, overlays |
| Minigames / score | rec room score/chain and game over | distinct mini-game memory contexts, BCD/packed fields and leaderboard submission conditions |
| Restrictions | no damage/no cap/no jump | per-frame negative conditions; input flags and start/end event boundaries |
| Save/reload | save, restart, reload different slot | no synthetic triggers from persistent flags, no destructive saves |
| System | VBlank, ARM7/ARM9, DTCM, overlay, IRQ, audio | 60Hz semantic evaluation and dropped/missed frames, cache, memory validity, freezes and battery |
| RA compliance | official set revisions, hash matching, official client authorization | metadata revision / no forged awards / no credentials in repository |

**Critical performance constraint:** 0.4.4 scans **1,024 bytes every ~120 frames** merely to prove memory changes. This is not enough for time-limited conditions. The full-set phase should use the original DScheevos / `rcheevos` per-frame watched-address snapshot engine; instrument precisely the addresses required by the *actual* set, protect game execution, and measure dropped frames/IRQ/idle budget before hardware deployment. No full 4 MB scan at 60 Hz.

## Gates before a physical 0.4.5/0.4.6 candidate

- **Gate 1 metadata coverage:** load genuine game 9983 catalog, produce complete ID list and revision SHA256. Flag uncovered categories/unknown or demoted/subsets separately. No hardcoded assumption that 157 is immutable.
- **Gate 2 real condition coverage:** obtain authorized game patch, match IDs/digests, confirm triggers are raw/parseable and build a *dependency graph using real rcheevos parser* (not regex alone), including main RAM, DTCM, pointer/indirect reads and invalid ranges.
- **Gate 3 host differential:** synthesize/replay framed A/B snapshots for each logic family against pinned `rcheevos` and a reference runtime; count evaluated/skipped/disabled/unknown. Never infer an unlock from a title.
- **Gate 4 real DSi spectator:** new isolated build with the real set, no auth/awards, confirm 60 Hz frames, stable audio/input/save, CPU budget, stats and real events for stars/coins/lives/time. Fail closed if any source/ABI mismatch or memory overlap.
- **Gate 5 compliance:** only after official partner/client requirements are addressed, design credentials, secure networking and authorized real award handling. No uncontrolled bulk unlock submissions.

**Bottom line:** 045 builds the scalable *coverage/inventory layer*. All 157 official achievements have **NOT** been individually verified on the DSi; this requires real set definitions, hardware measurements and tests. Keep 044 as physical baseline.
