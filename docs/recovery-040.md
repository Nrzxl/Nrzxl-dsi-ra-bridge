# DSi RA Bridge — checkpoint integrado 0.4.0 (19/11/2026)

## Decisão de engenharia

**Não repetir o ciclo de microtestes 034T/U/V e não retornar à vinculação de `Wifi_TWL_Update` no ARM7 customizado BlocksDS sem um motivo novo.** Reutilizar as versões já produzidas: transporte real 030 e observador independente 033. `040` é um checkpoint de recuperação e **um ensaio físico consolidado**, não uma reimplementação do driver, novo Wi-Fi em segundo jogo nem uma release de conquistas.

## Fontes e evidência

- Fonte física de rede **030**: `feat/dsi-ra-bridge-live-transport-030` HEAD `9c4dd0d9d15c46354b29fa792eefe3087aa6f9f1`, GitHub Actions [#44073752051](https://github.com/Nrzxl/Nrzxl-dsi-ra-bridge/actions/runs/44073752051). Base `devkitpro/devkitarm` + libnds/Calico e ARM7 padrão SDK. Pelo Flipnote Lenny → HBMenu no DSi XL, relatório do usuário e JSON da 031 confirmaram **600 UDP snapshots a 9.9712 Hz**, RTT 4.4227ms, sem erros CRC, com 71 duplicatas e 13 mensagens malformadas. Números representam o teste 030, não 031/032/033.
- Observador e segundo `.nds` **033**: `feat/dsi-ra-bridge-independent-nds-observer-033` HEAD `2529214498aaefea5d9ec5c281165b0f02eb341e`, GitHub Actions [#44155031464](https://github.com/Nrzxl/Nrzxl-dsi-ra-bridge/actions/runs/44155031464). Em melonDS **DS/NTR FreeBIOS**, `Fixture_B_033_control.nds`, `Fixture_B_033_observed.nds`, `Launcher_A_033.nds` passaram; chainload com **2154 frames observados, 1200 registros salvos, CRC PASS** e progresso após buffer cheio. `full_hook_cpu_time=NOT_MEASURED`, `official_awards=0`.
- **Técnica 033:** launcher A (`dsi/launcher-033-gpl/source/main.c`) bloqueia a execução caso `!isDSiMode()` ou não consiga `fatInitDefault()` / `stat("sd:/")` / validação CRC exata da Fixture observada. Faz chainload por `runNdsFile` de código do HBMenu sob GPL. O observador é um hook ARM9 em *fixture* sintético independente; ARM7 original é preservado. DSi XL e Flipnote Lenny não foram validados na versão 033. Não extrapolar emulação DS/NTR para carregamento DSi/TWL.
- **034R/S:** ARM7 custom de BlocksDS com `Wifi_TWL_Update` apenas vinculado WHITE no hardware, mas `.twl` canary, AES, SDIO isolados PASS. Esse caminho é distinto da stack padrão 030/033.

## Arquivos do usuário inspecionados (upload 19/11)

- `DSi_RA_Bridge_033-2529214498aaefea5d9ec5c281165b0f02eb341e.zip`: a cópia do ZIP SD interno tem SHA256 `21b7844a63a16ff99b7ac7cafa0d07b546994008c9051a466d1cad7a5b1835d8`; corresponding source zip tem `951e69e783ae03efc6a335c55ddc54a0b6c7fb34c26260e29f5cc57e03650d04`.
- Binários preservados bitwise: `Fixture_B_033_control.nds` SHA256 `524ed6166af75afc4ea88791c359d1c0d6071b3194ee112952842d48c179313e` (267264 B); `Launcher_A_033.nds` SHA256 `5e2e0a785c2808836eb5a74bc6620f79d5f17b1722cc27d4a7c066133976b9ad` (265216 B); `Fixture_B_033_observed.nds` SHA256 `5c30731de87f1f45f6e08ea8e54ec008b8b82f245aa6f5847b5fa8429f8e141a` (2479104 B). Nenhum dos três foi alterado.
- `DSi_RA_Bridge_033_Windows-2529214498aaefea5d9ec5c281165b0f02eb341e.zip` inclui o decoder Python, o avaliador rcheevos local `engine/dsirb_live.exe`, o hash Nintendo DS e o utilitário HELLO-only-032. Teste de leitura `decode.py` sobre `emulation/chainload.ram` do ZIP enviado retornou PASS, 1200 registros com provenance **NDS_EMULATOR**, não HARDWARE_EXPORT.
- Gerado kit local `DSi_RA_Bridge_040_Kit_Unico_033.zip` SHA256 `3d695c6084321497c2e16faf27514d757c01c9f0b8d70888cfebb47d9a8f4e44`, que reorganiza arquivos originais, inclui `verificar_040.py`, `VERIFICAR_040.cmd`, `ANALISAR_OBS_040.cmd`, guia e fontes GPL, sem alterar nenhum `.nds`. O arquivo é uma entrega da conversa e não foi publicado como release/artefato GitHub; **não inventar URL GitHub para esse kit**.

## Plano físico fechado: 1 sessão e 2 lançamentos, sem rede

1. BACKUP do SD, DSi desligado. Verificar pacote com `VERIFICAR_040.cmd`. Copiar **somente** `SD_COPIAR/nds/DSiRABridge_033` e `SD_COPIAR/DSiRABridge_033` para os mesmos caminhos novos na raiz do SD interno. Não sobrescrever diretórios existentes nem modificar `boot.nds`, `private`, `_nds`, R4, TWiLight, nds-bootstrap, NAND ou Unlaunch.
2. **Controle:** Flipnote Lenny → HBMenu → `Fixture_B_033_control.nds`. Aguardar 35 s; contador deve avançar, A/B devem mudar cor. X deve informar ausência de janela marcada; não há observador e não deve exportar. Se falhar, STOP sem tentar Launcher.
3. **Launcher:** reiniciar HBMenu → `Launcher_A_033.nds`. Exigir `Fixture integrity PASS`, modo **DSi**, e `sd:/` presente. Se `BLOCKED` por modo DSi, SD ou fixture, **capturar texto e STOP**; não mexer no desbloqueio.
4. **Chainload e observação:** só após gate PASS, A uma vez para iniciar Fixture B instrumentada; aguardar 35 s, A/B, X para exportar `sd:/DSiRABridge_033/OBSnnn.bin` com 53.248 bytes, esperar 30 s mais com contador progredindo. Desligar antes de remover o SD.
5. No Windows, copiar OBS para PC e arrastar em `ANALISAR_OBS_040.cmd` no kit. O decoder aceita apenas `HARDWARE_EXPORT`, verifica 1200 registros, CRC, ordem, stack guard e 1800+ frames, e avalia apenas LOCAL_TEST_ONLY. Resultado JSON é o comprovante, sem uploads automáticos.

## Diagnóstico orientado à causa, não séries intermináveis

- Se controle não inicia, problema de inicialização do `.nds`/ambiente antes do launcher; comparar 030 e controle 033 pelo mesmo caminho.
- Se controle inicia mas `Launcher A` diz `BLOCKED: require DSi mode` / `no sd:/`, analisar diferença de modo DSi/SD na cadeia Lenny→HBMenu; não culpar DSWiFi.
- Se loader passa integridade mas chainload falha, focar `runNdsFile`, bootstub, ARM7i/MBK e formato de `.nds`; não repetir microprobes Wi-Fi.
- Se chainload e OBS são PASS, validar persistência real do observador no **segundo homebrew**, depois integrar transporte 030 por estágios. Conquistas oficiais seguem bloqueadas até implementação legítima e compatibilidade rcheevos/rc_client e aprovação necessária.

**Estado:** 030 WIFI PHYSICAL PASS (dados controlados); 033 EMULATOR PASS, DSi física NOT_RUN; 034S diagnóstico PHYSICAL PASS; 040 single-round kit SHA VERIFIED, observador físico NOT_RUN. Não há desenvolvimento assíncrono ou claims de solução funcional antes do teste.