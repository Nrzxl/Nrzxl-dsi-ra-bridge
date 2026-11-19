# DSi RA Bridge 0.3.4-S — Teste isolado de TWL/AES/SDIO

## Estado físico anterior
- DSi XL, Flipnote Lenny → HBMenu: R0 e R1 iniciaram; R2 TWL_LINK ficou branco. **Não repetir R2**.
- P0 teve STAGE1+STAGE2 REACHED confirmados. Isso não confirma comunicação nos testes S ainda.
- SDK BlocksDS 1.24.0: script ds_arm7.ld coloca .twl em 0x03000000; CRT0 só copia/zera se detectar DSi. Não há leitura do estado real MBK/SCFG.

Fontes SDK:
https://github.com/blocksds/sdk/blob/v1.24.0/sys/crts/ds_arm7.ld
https://github.com/blocksds/sdk/blob/v1.24.0/sys/crts/ds_arm7_crt0.s

## Variantes e o que isolam

| Ordem | Arquivo | Alteração |
|---|---|---|
| S0 | DSIRB_034S_CONTROL.nds | ARM7/ARM9 idênticos ao controle R0 |
| S1 | DSIRB_034S_TWL_CANARY.nds | Somente um canário mínimo em .twl.text retido e nunca chamado |
| S2 | DSIRB_034S_AES_SYMBOL.nds | Linker retém somente o símbolo alvo AES mbedtls_internal_aes_encrypt |
| S3 | DSIRB_034S_SDIO_SYMBOL.nds | Linker retém somente o símbolo alvo wifi_sdio_send_command |

S2/S3 são independentes e podem agregar dependências transitivas. O arquivo AB_034S.md lista esses objetos. Nenhuma função vinculada é chamada. Não inicializa Wi-Fi, não acessa arquivos nem configura rede.

## Ordem protegida de teste físico
1. DSi desligado. Confira backup SD. Baixe artefato 034S de workflow SUCCESS; extraia ZIP interno. Copie somente nds/DSiRABridge_034S para a pasta nds do SD.
2. Preserve boot.nds, _nds, private, TWiLight++, NAND, Unlaunch e o exploit.
3. Teste **S0 CONTROL** primeiro pelo Flipnote Lenny → HBMenu. Esperado MAIN YES, STAGE1+2 REACHED e LOOP ALIVE crescendo. Se branco, POWER e PARAR.
4. Só se S0 PASS → **S1 TWL_CANARY**. Se branco, POWER e PARAR; S2/S3 BLOQUEADOS.
5. Só se S1 PASS → **S2 AES_SYMBOL**. Se branco, POWER e PARAR; S3 BLOQUEADO.
6. Só se S2 PASS → **S3 SDIO_SYMBOL**. Se branco, POWER e PARAR. Nunca repetir binário que deu branco.
7. Informe o primeiro teste com falha ou os estados dos quatro (MAIN, STAGE 1 e STAGE 2, LOOP).

## Interpretação conservadora
- S1 WHITE: mera referência a rotina .twl mínima pode ser relevante para o carregamento/CRT0.
- S1 PASS, S2 WHITE: dependências crypto/AES aparecem no caminho da regressão.
- S1+S2 PASS, S3 WHITE: dependências SDIO aparecem no caminho da regressão.
- Todos PASS: não reproduzido com esses subconjuntos; focar outras dependências TWL/combinação.

A presença dos símbolos no ELF não prova execução ou causa raiz. Sem conexão Wi-Fi, jogos, RetroAchievements, modificação NAND, merge, OTA ou release.