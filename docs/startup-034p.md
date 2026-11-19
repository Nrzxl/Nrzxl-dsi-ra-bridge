# DSi RA Bridge 0.3.4-P — link DSWiFi por símbolo, a partir do O2 aprovado fisicamente

## Histórico e hipótese

**No DSi XL via Flipnote Lenny → HBMenu**, O0 UI_ONLY, O1 SEND_ONLY e O2 RX_POLL abriram `MAIN REACHED: YES`. No O2, o usuário confirmou explicitamente **`STAGE 1: REACHED` e `STAGE 2: REACHED`**, demonstrando envio ARM7 → recebimento ARM9 no canal FIFO_USER_03 em hardware real. O contador continuando após o recebimento não foi confirmado separadamente.

O SDK1.24 com núcleos oficiais ARM7 Wi-Fi K1 e J1 produziu duas telas brancas; o mesmo ocorreu no SDK1.25 M1; o N0 (SDK1.25 com marcadores FIFO) piscou e ficou branco. O0/O1/O2 SDK1.24 funcionaram. L0/L1 com padding NWRAM funcionaram. Queremos agora **isolar vinculação de símbolos** em cima do O2, sem chamar essas funções e sem adicionar funções de rede no ARM9.

Referências: [BlocksDS ARM7 cores](https://github.com/blocksds/sdk/blob/v1.25.0/sys/arm7/main_core/source/main.c), [DSWiFi IPC](https://github.com/blocksds/dswifi/blob/master/source/arm7/ipc.c), [DSWiFi Update](https://github.com/blocksds/dswifi/blob/master/source/arm7/update.c), [memória DSi/NWRAM](https://blocksds.skylyrac.net/docs/internal/memory_map/). Essas referências descrevem o projeto, mas não provam a causa raiz do travamento.

## 3 executáveis com uma mudança por vez

| Ordem | Arquivo | ARM7 | ARM9 |
|---|---|---|---|
| P0 | `DSIRB_034P_CONTROL.nds` | **binário idêntico** ao ARM7 do O2 | **binário idêntico** ao ARM9 do O2 |
| P1 | `DSIRB_034P_UPDATE_LINK.nds` | mesmo ARM7, com `-ldswifi7` e apenas **referência de endereço de `Wifi_Update`** | idêntico ao P0 |
| P2 | `DSIRB_034P_FIFO_LINK.nds` | mesmo que P1, com referência adicional de endereço de **`installWifiFIFO`** | idêntico ao P0 |

Em P1 e P2 ponteiros de função são referenciados por barreira de compilador vazia, sem chamar essas funções. Isso faz o linker incluir código e dependências relevantes, que podem afetar o boot. O aplicativo **não inicializa Wi-Fi nem faz conexão**, embora o código vinculado ainda possa alterar layout de memória/CRT0.

**SDK fixado v1.24.0:** `skylyrac/blocksds:slim-v1.24.0@sha256:779f6193d1030c62e60d1f0f39c3e32cf4045c0bd224a45c0ceadf9d9ab01a51`.

GitHub Actions compila novamente O2 para comparação e compara diretamente os bytes das seções ARM7/ARM9 contidas nos quatro arquivos NDS, além de verificar símbolos ELF, segurança de fonte, cabeçalhos e footprint estático. **Compilação não é prova de funcionamento físico.**

## Teste físico de segurança (somente após CI SUCCESS)

1. Com DSi XL **desligado**, faça ou confira backup do SD. Extraia o pacote de artifacts `DSi_RA_Bridge_034P_DSWIFI_SYMBOL_GATES_SD_ONLY` (inclui ZIP interno).
2. Copie **somente** a pasta `nds/DSiRABridge_034P` para `D:\nds\DSiRABridge_034P\` (troque D pela letra do cartão). Não substitua `boot.nds`, `private/`, `_nds/`, TWiLight++, nem altere NAND, Unlaunch ou configuração do exploit.
3. Flipnote Lenny → HBMenu: execute **P0 CONTROL primeiro**. Esperado `MAIN REACHED: YES`, `STAGE 1: REACHED` e `STAGE 2: REACHED` (podem levar alguns quadros), contador `LOOP ALIVE` progredindo. START para sair. Se travar ou ficar branco, desligue pelo POWER e **PARE: não teste P1/P2**.
4. **Só se P0 PASS**, execute **P1 UPDATE_LINK** uma vez. Esperado mesma UI e STAGE1/2 REACHED. Se branco, desligue POWER, **pare: não teste P2**.
5. **Só se P1 PASS**, execute **P2 FIFO_LINK** uma vez. Esperado mesma UI e STAGE1/2 REACHED. Se branco, desligue POWER e pare. Não repetir nem testar executáveis anteriormente WHITE.
6. Registre exatamente se aparece `MAIN REACHED`, `STAGE 1`, `STAGE 2`, `LOOP ALIVE` ou apenas a tela do HBMenu (um flash não prova execução ARM9). Não configurar Wi-Fi, não carregar ROM e não digitar credenciais.

## Resultados possíveis

- **P0 PASS, P1 WHITE:** presença de `Wifi_Update` e seus objetos/dependências no ARM7 foi suficiente para reproduzir branco **sem chamar a função**. O próprio `Wifi_Update` executando não é o culpado demonstrado.
- **P0+P1 PASS, P2 WHITE:** a adição de `installWifiFIFO` e seus objetos/dependências correlaciona-se com branco; não houve chamada de instalação FIFO.
- **P0+P1+P2 PASS:** esse subconjunto de código DSWiFi não reproduz o sintoma no SDK1.24 com O2. Próxima etapa deverá separar chamadas reais de inicialização ou configuração de hardware, não supor funcionamento de Wi-Fi.
- **P0 WHITE:** controle inválido ou condição do ambiente mudou; não testar links.

Sem conexão de rede, jogo, conquistas oficiais, alterações NAND/Unlaunch. Estado físico de P0/P1/P2: **NOT_RUN** até relato.