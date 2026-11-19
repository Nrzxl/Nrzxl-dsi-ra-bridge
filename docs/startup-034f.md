# DSi RA Bridge 0.3.4-F — teste físico de inicialização por estágios

Dois testes 0.3.4-E reais foram **PASS**: `DEVKIT` e `BLOCKS`. Entretanto, 0.3.4-C e D dão duas telas brancas imediatamente e o Scout 034B (mesmo hash da build oficial) não abre neste momento. Não inferir culpado sem mais evidências.

Esses três aplicativos 034F não carregam **nenhum jogo**, não interagem com RetroAchievements, não iniciam sessão, não conectam Wi-Fi, não escrevem arquivos no SD e não alteram `boot.nds`, `private/`, TWiLight++, NAND nem Unlaunch. **F3 tenta apenas montar o SD** após confirmação manual, o que acessa o cartão para leitura; nenhum comando de escrita de arquivo foi implementado. ARM7 custom corresponde ao `dscheevos/launcher/arm7/source/main.c` em `skierrz/dscheevos@59e9978be7b9c3788357ef0a609caf9dc8ea74f3` (licença Zlib, mantido header SPDX).

## Arquivos e significado

| Experimento | O que muda em relação ao anterior | Tela esperada |
| --- | --- | --- |
| **F1 UI** `DSIRB_034F_UI.nds` | BlocksDS padrão (034E B comprovado), mas inicializa as duas telas como a interface DScheevos (`consoleInit`/VRAM) | `DSIRB 034F UI TEST`, `MAIN REACHED: YES` |
| **F2 ARM7** `DSIRB_034F_ARM7.nds` | Mantém o código ARM9 F1 e substitui **apenas** o ARM7 padrão pelo ARM7 DSWiFi personalizado do DScheevos | `DSIRB 034F ARM7 TEST`, `MAIN REACHED: YES` |
| **F3 FAT** `DSIRB_034F_FAT.nds` | Mantém UI e ARM7 F2, vincula suporte ao SD e testa `fatInitDefault()` **somente depois de apertar A** | Primeiro `MAIN REACHED: YES`; depois `FAT MOUNT: YES/NO` |

Essas etapas **não** isolam todos os fatores de compilação/tempo de execução (F3 também vincula DSWiFi9); servem apenas para orientar investigação futura sem risco de inicializar um retail loader.

## Como testar com segurança

1. Console **desligado**, faça backup do SD. Baixe artefato `DSi_RA_Bridge_034F_STARTUP_STAGES_SD_ONLY` no Actions, extraia o ZIP de dentro do artefato no PC.
2. Copie **apenas** `nds/DSiRABridge_034F` para `D:\nds\DSiRABridge_034F` (ajuste a letra da unidade; não copie outros arquivos nem substitua pastas do sistema).
3. No DSi XL, abra pelo Flipnote Lenny → HBMenu **F1 UI**. Anote tela (texto vs branco). START sai. Se falhar, DESLIGUE pelo POWER e **não teste os outros F**.
4. Se F1 PASS, abra **F2 ARM7**. Anote tela. Se branco, desligue e não teste F3.
5. Se F2 PASS, abra **F3 FAT**. Na primeira tela, **ainda sem montar SD**, aperte START para parar se não quiser continuar. Para testar FAT, pressione A uma vez. Anote resultado: `FAT MOUNT YES`, `NO`, congelou em `attempting...`, ou tela branca anterior à primeira tela. START retorna; se congelar, POWER.
6. Poste somente o último resultado F1/F2/F3 e a mensagem exibida. Não envie ROMs, saves, dados de login ou backup do SD.

## Interpretação

- F1 WHITE → UI VRAM/console personalizado pode conflitar com hardware/ambiente, **não prova** defeito do ARM7.
- F1 PASS + F2 WHITE → investigar o ARM7 DSWiFi personalizado e handoff/IPC.
- F1+F2 PASS + F3 WHITE/STALL → investigar `fatInitDefault`, inicialização do SD, DSWiFi9, IPC e estado da interface.
- Todos PASS → resta explorar tamanho/layout do binário completo e inicialização de bibliotecas, TLS, rcheevos e outras dependências.
- Resultado diferente não deve levar a conclusões fortes antes de revisar os marcadores e repetir teste somente quando for seguro.

**STATUS:** Builds automaticamente validadas não são comprovação de execução no DSi. Retail boot BLOCKED; sem achievements oficiais. Não insistir nos Launchers 034C/034D.
