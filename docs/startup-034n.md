# 0.3.4-N — ARM7 startup stages + DSWiFi Wifi_Update symbol-only link

## Razão técnica

Histórico DSi XL físico por Flipnote Lenny → HBMenu:
- L0 CONTROL e L1 NWRAM PAD (footprint DSi-only maior) PASS.
- SDK 1.24 K0 minimal PASS / K1 official DSWiFi WHITE.
- SDK 1.25 M0 minimal PASS / M1 official DSWiFi WHITE.
- H1 LINK via `installWifiFIFO` mesmo sem chamada WHITE.

Pesquisa no [ARM7 core oficial SDK 1.25.0](https://github.com/blocksds/sdk/blob/v1.25.0/sys/arm7/main_core/source/main.c) confirma `installWifiFIFO` após `fifoInit` e `Wifi_Update` no VBlank apenas quando DSWiFi habilitado. Em [DSWiFi ARM7 ipc.c](https://github.com/blocksds/dswifi/blob/master/source/arm7/ipc.c), `installWifiFIFO` registra handlers FIFO, não estabelece rede diretamente; no [update.c](https://github.com/blocksds/dswifi/blob/master/source/arm7/update.c), `Wifi_Update` retorna quando `WifiData` é NULL. Isso NÃO exclui falha do CRT0/linker/TWL ou dependências ligadas no binário.

Referências: https://blocksds.skylyrac.net/docs/internal/build_process/ (ARM7 CRT0, sincronização de CPUs), https://blocksds.skylyrac.net/docs/internal/memory_map/ (NWRAM/MBK), https://blocksds.skylyrac.net/tutorial/intermediate/using_the_arm7/ (FIFO e cores).

## Experimento

Mesmo código ARM9 nas duas builds: tela com `MAIN REACHED: YES`, dois marcadores e contador LOOP ALIVE. O ARM7 emite dois valores em `FIFO_USER_03`:
- **STAGE 1**: ARM7 já executou `fifoInit`, enviou o marcador antes de instalar serviços.
- **STAGE 2**: ARM7 já instalou serviços básicos e habilitou VBlank, enviou marcador de conclusão.

N0: `DSIRB_034N_CORE.nds` — ARM7 básico sem DSWiFi, mas com os marcadores.
N1: `DSIRB_034N_UPDATE_LINK.nds` — mesmo ARM7 básico e marcadores; compila com DSWiFi7 e **mantém somente endereço do símbolo `Wifi_Update`**, sem jamais chamá-lo. Isso força dependências desse símbolo a entrar no executável. Não instala Wi-Fi FIFO e não tenta conexão. `installWifiFIFO` é uma variável distinta já testada no H1; N1 testa uma rota diferente de vínculo.

Um branco antes de MAIN REACHED não prova que o ARM7 não chegou em main: o boot CRT0 sincroniza CPUs e a interface pode não iniciar. Marcadores FIFO só ficam visíveis **se ARM9 conseguiu mostrar a interface**. O experimento não escreve logs em SD nem altera memória de firmware.

## Segurança e instalação

1. Com DSi completamente desligado, fazer backup de todo SD (ou conferir backup existente).
2. Baixar o artefato `DSi_RA_Bridge_034N_STAGES_LINK_UPDATE_SD_ONLY` no GitHub Actions da branch QA. Extrair o ZIP interno. Copiar **somente** `nds/DSiRABridge_034N` à pasta `nds` do SD; não substituir `boot.nds`, `private/`, `_nds/`, TWiLight++, NAND, ou instalar Unlaunch.
3. No Flipnote Lenny → HBMenu, abrir **N0 CORE** primeiro. Esperado `MAIN REACHED: YES`, `STAGE 1: REACHED`, `STAGE 2: REACHED`, `LOOP ALIVE` avançando. START sai. Se telas brancas, desligar POWER, PARAR, não executar N1.
4. **Somente se N0 PASS**, abrir **N1 UPDATE_LINK** UMA VEZ. Relatar a presença/ausência de MAIN, STAGE 1, STAGE 2 e contador, ou se duas telas ficam brancas. Em travamento, desligar POWER e PARAR; não insistir.
5. Não executar 034G FIFO, H1 LINK, K1 WIFI_ONLY, J1 WIFI_CORE, M1 WIFI125 novamente. Não abrir jogos/ROMs nem configurar Wi-Fi durante o diagnóstico.

## Interpretação

N0 PASS / N1 WHITE: a mera vinculação das dependências de `Wifi_Update`, sem chamada de Wi-Fi, é suficiente para reproduzir o sintoma. Investigar seções carregadas, inicializadores e referências de código/data; não concluir bug de `Wifi_Update` em execução.
N0 PASS / N1 PASS: a mera vinculação da rota `Wifi_Update` NÃO reproduziu o sintoma; aumenta prioridade da rota `installWifiFIFO` e/ou dependências que ela agrega, compare mapas ELF. Nenhum Wi-Fi foi inicializado.
N0 WHITE: não testar N1; possível problema introduzido pelo próprio mecanismo de marcadores ou empacotamento, revisar antes.

Uma tela com marcadores no N1 não prova conexão Wi-Fi, jogos comerciais nem RetroAchievements. CI verifica somente construções estáticas; hardware status NOT_RUN até a observação do usuário.