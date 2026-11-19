# DSi RA Bridge 0.3.4-H — localizar o travamento do Wi-Fi FIFO

Os resultados físicos informados: 034E A e B PASS; 034F F1 UI PASS; 034F F2 ARM7 WHITE; 034G G1 CORE PASS; 034G G2 FIFO **WHITE / FAIL**. Não executar 034G G3.

O G2 introduziu **dois fatores de uma vez**: linkedição da biblioteca `dswifi7` e chamada `installWifiFIFO()` durante o boot ARM7. Esta versão H separa as duas coisas. A 034H permanece diagnóstica: **sem ROM, RetroAchievements, nds-bootstrap, Wi-Fi ligado/associado, acesso a SD pelo programa, escrita, logins, saves ou NAND**.

| Ordem | Arquivo | Objetivo | Como interpretar |
|---|---|---|---|
| H1 LINK | `DSIRB_034H_LINK.nds` | Mesmo ARM7 básico do G1, **DSWiFi7 realmente vinculada por símbolo**, mas **NUNCA chama** `installWifiFIFO` | Se passar, carregar o código da biblioteca não basta para reproduzir o travamento |
| H2 GATE | `DSIRB_034H_GATE.nds` | Tela normal inicia **antes** de qualquer chamada WiFi. Somente após pressionar A solicita ao ARM7 `installWifiFIFO()` e espera retorno | Se H2 mostrar a tela inicial mas travar após A, a chamada/ação do FIFO é suspeita |

**Isolamento com limites:** estes testes diferem em eventos IPC; H1 PASS e H2 falhar antes de A podem refletir diferenças de handler/código e não necessariamente `installWifiFIFO`. Não afirmar causa definitiva com um só resultado.

## Instruções físicas

1. Com DSi **desligado**, confirme backup do cartão. Baixe o artefato do GitHub Actions e extraia o ZIP interior.
2. Copie somente a pasta **`nds/DSiRABridge_034H`** para a mesma pasta no cartão (`D:\nds\DSiRABridge_034H`, se ainda for D:). Não substituir `boot.nds`, `private/`, `_nds/`, TWiLight++.
3. Abrir primeiro `DSIRB_034H_LINK.nds` no Flipnote Lenny → HBMenu. Se mostrar `MAIN REACHED: YES`, é PASS. START sai. Se ficar branco, desligue console e pare, **não teste H2**.
4. Se H1 PASS, abrir `DSIRB_034H_GATE.nds`. Ele deve mostrar `MAIN REACHED: YES` **antes de qualquer tentativa WiFi**. **Primeiro relate se a tela inicial aparece**; o usuário pode sair sem chamar WiFi com START. Somente numa sessão de teste separada, se explicitamente desejar, pressionar A para solicitar `installWifiFIFO`. Se a tela ficar branca/travar, desligar pelo POWER e parar, sem repetir.
5. Informe H1 PASS/WHITE, H2 antes de A PASS/WHITE e, **somente se testou A**, se apareceu `ARM7 installWifiFIFO returned.` ou travou. Não enviar ROMs ou saves.

**G3 UPDATE, F3 FAT e os launchers 034C/034D seguem bloqueados.** Compilar não valida execução física; conquistas oficiais e carregamento comercial continuam NÃO DEMONSTRADOS.
