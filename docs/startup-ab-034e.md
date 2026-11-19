# DSi RA Bridge 034E — startup A/B isolado
Experimento controlado de inicialização para diagnosticar as **telas brancas imediatas** em 034C e 034D (sem S0, sem launcher.log).

**Não** é um carregador de jogos, não executa ROM, não contém módulos de conquistas, não acessa Wi-Fi, não abre/monta/escreve no SD, não toca NAND, Unlaunch, boot.nds ou TWiLight++.

| Arquivo | Plataforma de compilação | Dependências em execução |
|---|---|---|
| `DSIRB_034E_DEVKIT.nds` | devkitARM/libnds, família comprovada no scout 034B | ARM7 padrão |
| `DSIRB_034E_BLOCKS.nds` | BlocksDS/libnds 2 com ARM7 **padrão**, sem ARM7 custom do DScheevos | ARM7 padrão |

**Não misturar esses executáveis com a 034C/034D.**

## Teste físico, um por vez

1. Com o DSi desligado, faça backup do SD. Extraia o ZIP no computador. Copie **somente** `nds/DSiRABridge_034E/` para a mesma pasta no SD. Não copie para `_nds/` ou raiz e não substitua `boot.nds`.
2. Inicie pelo caminho Flipnote Lenny → HBMenu, como fez no scout 034B.
3. Abra primeiro `DSIRB_034E_DEVKIT.nds`. O resultado esperado é texto "DSIRB 034E STARTUP A", "MAIN REACHED: YES", "DSi mode: YES". Pressione START ou desligue para retornar ao menu.
4. Abra `DSIRB_034E_BLOCKS.nds`. Procure "DSIRB 034E STARTUP B" e "MAIN REACHED: YES". Pressione START para sair.
5. Se algum deles ficar branco, **não repita nem force**: desligue pelo POWER, depois de alguns segundos religue e volte somente ao homebrew estável 034B se quiser comprovar que o ambiente continua íntegro.
6. Informe somente: A exibiu texto? B exibiu texto? DSi mode mostrado? Não envie saves, ROMs ou conteúdo privado do SD.

## Como interpretar sem extrapolar

- **A PASS / B WHITE:** suspeita fortalecida de incompatibilidade de inicialização BlocksDS padrão com esse caminho de boot ou com esse hardware. Ainda não aponta uma causa única.
- **A PASS / B PASS:** a biblioteca/boot mínima BlocksDS funciona; próximos suspeitos são o custom ARM7/DSWiFi, demais dependências pesadas, memória ou o layout do launcher DScheevos.
- **A WHITE / B WHITE:** diagnosticar HBMenu, SD, entrada pelo Flipnote e diferenças entre 034B e A antes de qualquer loader novo.
- **A WHITE / B PASS:** diferença inesperada na família devkitARM; repetir somente após revisão do binário, não insistir automaticamente.

Nem **S0 da 034D** nem a existência de `launcher.log` foram comprovados no hardware. O primeiro boot retail continua **BLOCKED**. Nenhuma conquista oficial pode ser obtida a partir deste experimento.
