# DSi RA Bridge 0.3.4-M — SDK 1.25.0 official ARM7 DSWiFi startup A/B

**Objetivo:** comparar o BlocksDS 1.24.0 (K0 minimal PASS, K1 DSWiFi WHITE fisicamente) com o BlocksDS 1.25.0, publicado em 05/11/2026, sem introduzir chamadas Wi-Fi no ARM9. O 034L L0/L1 PASS físico demonstrou que padding inerte NWRAM similar ao DSWiFi NÃO reproduziu a falha. A versão 1.25.0 mudou detecção de modo DSi em libnds, corrigiu Wifi_Update recursivo e problemas de timeout no DSWiFi, mas NENHUMA correção oficial foi descrita como solução para a tela branca anterior ao `main` no Flipnote Lenny.

Fontes: https://blocksds.skylyrac.net/docs/changelog/ (v1.25.0), https://blocksds.skylyrac.net/docs/guides/usage_notes/ (núcleos ARM7), https://blocksds.skylyrac.net/docs/internal/memory_map/ (MBK/NWRAM), https://blocksds.skylyrac.net/docs/guides/legacy_support/ (carregadores).

Novos executáveis, **idêntico código ARM9**:
- M0 `DSIRB_034M_BASE125.nds`: core oficial `arm7_minimal.elf` do SDK **1.25.0** (controle).
- M1 `DSIRB_034M_WIFI125.nds`: core oficial `arm7_dswifi.elf` do SDK **1.25.0**. Nenhuma chamada de inicialização ou conexão Wi-Fi é feita no ARM9. Contém driver no ARM7 que pode preparar recursos durante o boot.

CI compara também os núcleos oficiais da versão 1.24.0 K0/K1 sem alterá-los, gera relatórios de seções ELF e SHA256. O CI passar não comprova execução em DSi XL.

**Procedimento seguro:**
1. DSi XL completamente desligado, criar/conferir backup do SD no PC; não mudar arquivos de sistema.
2. No GitHub Actions, baixar artefato `DSi_RA_Bridge_034M_SDK125_ARM7_SD_ONLY` e extrair ZIP interior. Copiar *apenas* `nds/DSiRABridge_034M/` para `D:\nds\DSiRABridge_034M\` (ajustar letra da unidade). Nunca sobrescrever `boot.nds`, `private/`, `_nds/`, TWiLight++, NAND ou instalar Unlaunch.
3. Via Flipnote Lenny → HBMenu, abrir **M0 BASE125 primeiro**. Se mostrar `MAIN REACHED: YES` e contador `LOOP ALIVE` crescente, sair por START. Se tela branca, desligar POWER e **NÃO abrir M1**.
4. **Apenas se M0 PASS**, abrir **M1 WIFI125**. Registrar se mostra `MAIN REACHED: YES`/`LOOP ALIVE` ou fica branco. No primeiro branco, POWER e PARAR, não repetir.
5. Não digitar senhas, não configurar Wi-Fi, não carregar jogos, não executar os antigos Wi-Fi que falharam.

**Interpretação:** M0 PASS/M1 PASS indicaria que o núcleo Wi-Fi da versão 1.25 ou alterações do toolchain/CRT0 mudaram o comportamento (sem provar qual). M0 PASS/M1 WHITE indica que atualização 1.25 não resolve a falha de inicialização nessas condições. M0 WHITE implica investigar regressão de build/loader antes de M1. Não atribuir raiz sem depuração separada.

Status inicial: ambos HARDWARE NOT_RUN, official RA awards 0, retail monitor BLOCKED.