# DSi RA Bridge 0.3.4-O — contornar a tela branca do N0 isolando FIFO

## Situação e hipótese

Após sucesso físico L0/L1 (034L) sem DSWiFi, **N0 034N CORE mostrou um flash muito breve de uma tela e depois duas telas brancas**. Não sabemos se o flash era o ARM9 do N0 ou metadados da tela de lançamento do HBMenu. **N1 UPDATE_LINK não foi testado e não deve ser executado.**

Comparação de código confirma que N0 introduziu **dois envios ARM7 `fifoSendValue32(FIFO_USER_03)`**, **recepção ARM9 usando `fifoCheckValue32`/`fifoGetValue32`** e UI atualizada. A API FIFO do BlocksDS documenta que envio retorna status booleano e que mensagens podem ser lidas manualmente; não prova qual parte travou. Fonte: https://blocksds.skylyrac.net/tutorial/intermediate/using_the_arm7/

## Novo diagnóstico em três passos, sem DSWiFi

**SDK pinado BlocksDS 1.24.0**, o mesmo utilizado no 034L que passou fisicamente. Nenhuma chamada a DSWiFi, FAT/SD, rede, jogos, RA, MBK/SCFG ou NAND. CPU ARM7 continua com suas inicializações padrão de som/sistema/RTC.

| Etapa | Arquivo | Variável isolada |
|---|---|---|
| O0 | `DSIRB_034O_UI_ONLY.nds` | controle: ARM7 **byte-identical** a L0, nova UI com estágios sempre WAITING e contador; nenhum FIFO_USER_03 |
| O1 | `DSIRB_034O_SEND_ONLY.nds` | ARM9 **binário idêntico a O0**; adiciona somente dois `fifoSendValue32` no ARM7, sem leitura ARM9 |
| O2 | `DSIRB_034O_RX_POLL.nds` | ARM7 **binário idêntico a O1**; habilita apenas leitura FIFO_USER_03 no ARM9, até quatro mensagens por quadro |

CI compara os hashes ARM7 do L0 e O0, ARM9 do O0/O1 e ARM7 do O1/O2. Pacote só será considerado liberado com essa comparação + headers NDS e quatro testes de código PASS.

## Teste físico condicional (não repetir binários anteriores)

1. DSi XL desligado. Confirmar backup íntegro do SD. Não formatar e não alterar boot.nds, private/, _nds/, TWiLight++, NAND ou Unlaunch.
2. Baixar artefato `DSi_RA_Bridge_034O_FIFO_ISOLATION_SD_ONLY` no Actions; extrair o ZIP interno. Copiar **somente** `nds/DSiRABridge_034O/` para o SD na pasta `nds` (p. ex. `D:\nds\DSiRABridge_034O`).
3. No Flipnote Lenny → HBMenu, abrir **O0 `DSIRB_034O_UI_ONLY.nds`**. Deve exibir `MAIN REACHED: YES` e `LOOP ALIVE: ... frames` crescendo. STAGE 1/2 ficará `WAITING` intencionalmente. START sai. **Se ficar branco, POWER e PARAR; não testar O1/O2.**
4. **Somente se O0 PASS**, abrir **O1 `DSIRB_034O_SEND_ONLY.nds`**. Interface igual à O0 e também `WAITING`, porque receptor ARM9 está propositalmente desabilitado. Se ficar branco, POWER e PARAR; não testar O2.
5. **Somente se O1 PASS**, abrir **O2 `DSIRB_034O_RX_POLL.nds`**. Deve mostrar `STAGE 1: REACHED`, `STAGE 2: REACHED`, LOOP ALIVE. Na primeira tela branca, POWER e PARAR. Não repetir.
6. Relatar o primeiro teste que falhou ou os três estados, se passaram. Se só houve um flash, registrar se viu texto `MAIN REACHED`/estágios ou a ficha/ícone do HBMenu.

## Interpretação conservadora

O0 branco: nova UI ou empacotamento, não concluir que FIFO enviou algo. O0 PASS/O1 branco: introdução de `fifoSendValue32` ARM7 associada à regressão, não necessariamente prova deadlock. O0+O1 PASS/O2 branco: parte de recepção/polling ARM9 associada. Todos PASS: 034N foi afetado por outra diferença, possivelmente versão SDK 1.25 ou interação de código; não assumir que DSWiFi está resolvido.

Nenhum teste inclui driver Wi-Fi, conexão, jogos comerciais nem conquistas oficiais. Status físico NOT_RUN até relato do usuário.