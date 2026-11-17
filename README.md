# DSi RA Bridge 0.3.1 — estabilidade experimental
Branch: `fix/dsi-ra-bridge-network-stability-031` (base 030 preservada).

[Guia 031](docs/network-031.md) · [Auditoria](docs/audit-031.md) · [Próximo monitor](docs/monitor-031.md)

Executar `Start-Receiver-LAN.cmd` no pacote Windows. Sem alterar política PowerShell.
Build real e testes: workflow `network-stability-031.yml`; consulte o resultado do commit.
Hardware 031: **NOT_RUN** até nova evidência. Nenhuma submissão oficial RA.
Instalação aditiva em `sd:/nds/DSiRABridge_031/`; capturas/config em `sd:/DSiRABridge_031/`.
Preserve 020/030 e todos os arquivos estáveis do console.

---

# DSi RA Bridge 0.3.0 — transporte experimental

A versão Network 030 é independente do diagnóstico 020. Comece por docs/network-030.md.
A branch feat/dsi-ra-bridge-live-transport-030 compila NDS e receiver Windows via network-experimental.yml.
Rede física, WPA2 via Flipnote Lenny e monitor persistente continuam NOT_RUN até teste do usuário.
Não há autenticação RA, jogos reais ou submissões oficiais nesta versão.

## Histórico da versão 020

# DSi RA Bridge — 0.2.0 (experimental)

**Repository:** https://github.com/Nrzxl/Nrzxl-dsi-ra-bridge (PUBLIC; configured by owner)

**Validation status:** JavaScript unit tests 664 PASS; ARM `.nds` build not yet validated; physical DSi and official achievements NOT_RUN.

The ARM build is explicitly manual: Actions → ARM diagnostic manual 020 → Run workflow → choose experimental branch. No auto-release, no NAND modifications, no RetroAchievements submissions.

---

# DSi RA Bridge 0.2.0 — Fase 2

Estado atual: fontes e pipeline ARM preparados; BUILD ARM BLOCKED, DSi físico NOT_RUN.

Comece por docs/phase2-checkpoint.md. O inicializador cria uma pasta nova e não instala SDKs.
O workflow .github/workflows/arm-diagnostic-manual.yml é manual e não publica releases.
O guia docs/sd-test-020.txt só se aplica depois de existir o .nds validado.
Não há .nds fictício ou binário compilado nesta entrega de fontes.

## Checkpoint 010 preservado como histórico

# DSi RA Bridge 0.1.0 — fase experimental
Estado da entrega: código de diagnóstico e clientes preparados; build ARM BLOCKED.
Nenhum .nds compilado acompanha este pacote de fontes. Nenhuma execução no DSi
foi validada. Nenhuma conquista oficial foi enviada. Não é cliente RA aprovado.

## Primeiro uso no computador
1. Abra windows/bridge/viewer.html e clique em Gerar teste simulado.
2. Com Node instalado, execute: node tests/protocol-tests.cjs
3. Gere um arquivo: node windows/bridge/bridge.cjs simulate --out SIMULATED.drb
4. Reproduza: node windows/bridge/bridge.cjs replay --file SIMULATED.drb
5. Alternativa Python 3.8+: python windows/bridge/replay.py SIMULATED.drb

## Build
Consulte docs/build.md e execute scripts/Build-Diagnostic.ps1 somente após
instalar a imagem oficial inspecionada. O script não instala nada, não copia
para o cartão e só empacota quando dois builds produzem o mesmo SHA-256.
A compatibilidade da receita ainda depende de compilação real.

## DSi
O roteiro está em docs/sd-test.txt. Seu console usa Flipnote Lenny → HBMenu.
Não abrir fwTool, não instalar Unlaunch, não atualizar firmware e não substituir
a instalação funcional do R4. O diagnóstico não precisa de jogos ou saves.

## Escopo
A: diagnóstico limitado ao próprio buffer, código escrito; build BLOCKED.
B: espécime cooperativo no diagnóstico; monitor em outro jogo BLOCKED.
C: replay HTML/Node/Python e cliente UDP de diagnóstico escritos; rede NOT_RUN.
D: exemplo C com rcheevos preparado; compilação/execução NOT_RUN.

Os testes do protocolo JavaScript executaram 632 verificações neste atendimento.
Isso não valida o binário ARM, os sockets Windows, o rcheevos C ou o hardware.
Consulte docs/validation.md para o significado exato dos estados.

O pacote é removível e não contém código de escrita de NAND.
Origem runtime nos pacotes é autodeclarada: emuladores também podem produzi-la.
