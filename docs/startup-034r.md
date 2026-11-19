# DSi RA Bridge 0.3.4-R — caminho NTR vs TWL do DSWiFi

## Importante: uma hipótese de correção, não uma correção comprovada

Q mostrou que P0 ARM7+ARM9 base funciona com ambos STAGES REACHED, e P1 WHITE ao apenas vincular Wifi_Update sem chamá-la. O linker trouxe simultaneamente os subcaminhos `Wifi_NTR_Update` (.text tradicional do DS) e `Wifi_TWL_Update` (.twl do DSi) e mais 50 objetos de biblioteca.

Esta etapa tenta contornar a combinação de dependências **isolando cada caminho**. Nenhum executável liga o rádio, instala WifiFIFO, envia credenciais, faz conexão ou carrega jogos. O GitHub Actions confirma apenas integridade dos executáveis e qual código foi incluído; não pode comprovar o funcionamento no DSi XL.

| Ordem | Executável | Objetivo |
|---|---|---|
| R0 | `DSIRB_034R_CONTROL.nds` | ARM7 e ARM9 idênticos ao P0 físico PASS |
| R1 | `DSIRB_034R_NTR_LINK.nds` | vincula somente a rota `Wifi_NTR_Update` sem chamá-la |
| R2 | `DSIRB_034R_TWL_LINK.nds` | vincula somente `Wifi_TWL_Update` sem chamá-la; variante independente de R1 |

SDK idêntico ao controle `BlocksDS 1.24.0`, Docker com digest fixo, sem rede na compilação. Todos exibem os mesmos dois marcadores ARM7→ARM9 já confirmados.

## Instruções físicas com bloqueio em cascata

1. Com o DSi **desligado**, confirme o backup do cartão SD. Não altere `boot.nds`, `private/`, `_nds/`, TWiLight++, NAND, nem instale Unlaunch.
2. Baixe o artefato `DSi_RA_Bridge_034R_NTR_TWL_SPLIT_SD_ONLY` da execução CI **SUCCESS** e extraia o ZIP interno. Copie apenas `nds/DSiRABridge_034R/` à pasta `nds` do SD.
3. Abra o Flipnote Lenny → HBMenu e inicie **R0 CONTROL**. Esperado `MAIN REACHED YES`, `STAGE 1 REACHED`, `STAGE 2 REACHED`, `LOOP ALIVE` crescente. START sai. Se branco, POWER desligar; PARE e não execute R1/R2.
4. **Somente se R0 PASS**, abra **R1 NTR_LINK** uma vez. Se branco, POWER desligar; PARE. **Não execute R2** depois de uma falha R1.
5. **Somente se R1 PASS**, abra **R2 TWL_LINK** uma vez. Se branco, POWER desligar; PARE. Caso não travar, registrar se os dois STAGE chegaram a REACHED.
6. Não repetir os antigos binários conhecidos WHITE. Não usar Wi-Fi ou jogos; não modificar arquivos do exploit.

## Interpretação conservadora

- R0 PASS/R1 WHITE: até mesmo o subconjunto NTR (e suas dependências transitivas) causa a falha; investigar WRAM, .text, .bss e inicialização de carregamento.
- R0+R1 PASS/R2 WHITE: o subconjunto TWL introduz a condição de falha; priorizar mapeamento/cópia de NWRAM e compatibilidade do carregador com `.twl` real.
- R0+R1+R2 PASS: cada rota isolada funciona, mas o wrapper completo `Wifi_Update` (que inclui ambas) continua suspeito; avaliar combinação de layout e dependências e planejar driver seletivo.
- Em todos os casos, o funcionamento de Wi-Fi e RetroAchievements **ainda não está comprovado**.

Relatório estático adicional `AB_034R.md` com detalhes ELF e membros `.a` selecionados, mais SHA256 e traces. Branch QA isolada, sem merge/release.