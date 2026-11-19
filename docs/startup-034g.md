# DSi RA Bridge 034G — ARM7 personalizado isolado (diagnóstico após 034F)

**Evidência no hardware:** 034E A/B PASS, 034F F1 UI PASS, 034F F2 ARM7 WHITE/FAIL, 034F F3 FAT NÃO TESTAR.

Os três novos testes 034G usam a **mesma interface ARM9** de 034F F1, mas isolam pequenas porções do ARM7 personalizado, sem carregar jogos, montar SD, gravar arquivos, solicitar login, abrir rede, emitir conquistas ou alterar NAND/SCFG/Unlaunch. Contêm código derivado do ARM7 do DScheevos sob licença Zlib e preservam as notas de copyright.

| Ordem | Arquivo | Nova variável |
| --- | --- | --- |
| G1 | `DSIRB_034G_CORE.nds` | Base do ARM7 personalizado, **sem DSWiFi** |
| G2 | `DSIRB_034G_FIFO.nds` | Mesmo ARM7, **com** `installWifiFIFO()`, sem `Wifi_Update()` |
| G3 | `DSIRB_034G_UPDATE.nds` | Como G2, **mais** `Wifi_Update()` no VBlank (sem conexão) |

**Passos:** console totalmente desligado; backup do SD; baixar artefato do Actions e extrair ZIP interno no Windows; copiar **somente** `nds/DSiRABridge_034G/` para `D:\nds\DSiRABridge_034G` (ajustar letra, não sobrescrever `boot.nds`, `private` ou `_nds`). No DSi XL: Flipnote Lenny → HBMenu → executar G1. Se aparecer `MAIN REACHED: YES`, sair por START e prosseguir para G2. Se G2 passar, prosseguir para G3. **PARAR no primeiro branco**, desligar pelo POWER, não repetir automaticamente e não tentar F3/034C/034D.

Interpretação preliminar: G1 branco implica investigar estrutura custom ARM7 básica/handshake; G1 OK/G2 branco implica FIFO WiFi ou link DSWiFi7; G1+G2 OK/G3 branco implica VBlank `Wifi_Update()`; G1-G3 OK e F2 branco implica diferenças remanescentes como handover FIFO handler/freeze/estado de WiFi. Não atribuir causa específica sem evidência e comparação da execução.

**NOT_RUN no hardware até o usuário confirmar.** Build PASS apenas confirma compilação e formato. Nenhuma conquista oficial disponível nesse gate.
