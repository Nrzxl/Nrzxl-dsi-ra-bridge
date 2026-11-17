# Fontes e rastreabilidade
Consulta em 16/11/2026. Repositórios inspecionados por API/arquivos raw.
Clone local e execução dos projetos: BLOCKED pelo ambiente.
“Relatado” designa evidência do mantenedor; não teste reproduzido por nós.

| ID | Fonte primária | Uso |
|---|---|---|
| S1 | https://problemkaputt.de/gbatek.htm#dsmemorymaps | RAM, CPUs, TCM |
| S2 | https://problemkaputt.de/gbatek.htm#dsiscfgregisters | Controle do modo e permissões |
| S3 | https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/README.md | WIP, alvo e limites declarados |
| S4 | https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/docs/architecture.md | Reserva, fila e agendamento relatados |
| S5 | https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/dscheevos/module/src/module.c | Callback de memória e DTCM |
| S6 | https://github.com/skierrz/nds-bootstrap/blob/af351f096dd71a37e0e5b18d9709bcc0fb70342f/retail/bootloaderi/source/arm7/dscheevos_hooks.c | Instalação dos hooks e gates |
| S7 | https://github.com/Bakkerrrs/Retroachievements-DS-on-3DS/blob/4d60695487a5593531c0c395e8d4d1ae2ca91fad/retail/cardenginei/arm9/source/ra_reader.c | DSi excluído em ra_tick |
| S8 | https://github.com/Bakkerrrs/Retroachievements-DS-on-3DS/blob/4d60695487a5593531c0c395e8d4d1ae2ca91fad/docs/retroachievements.md | Evolução e experimentos relatados |
| S9 | https://github.com/Bakkerrrs/Retroachievements-DS-on-3DS/commit/f7dd6bc723c649346bd7fb610363b8f15ade684f | Falha relatada de rede durante jogo |
| S10 | https://github.com/DS-Homebrew/nds-bootstrap/blob/5e94d928d4ad0c8aea2b07145a0791e762513795/README.md | Modos, build e frontend |
| S11 | https://github.com/DS-Homebrew/nds-bootstrap/blob/5e94d928d4ad0c8aea2b07145a0791e762513795/retail/cardenginei/arm7/source/cardengine.c | myIrqHandlerVBlank, linha 1823 |
| S12 | https://github.com/DS-Homebrew/TWiLightMenu/blob/5d7ec54d402ff612577f57a6916a312740d71aeb/README.md | Componentes do frontend |
| S13 | https://github.com/DS-Homebrew/TWiLightMenu/commits/master/romsel_dsimenutheme/arm9/source/main.cpp | Histórico do lançamento |
| S14 | https://dsi.cfw.guide/faq.html | Flipnote Lenny e limitações |
| S15 | https://github.com/hacan359/xerabora/blob/98949c0efba151f16b234ba5b392b5241791f40e/protocol/PROTOCOL.md | Separação agente/cliente e snapshots |
| S16 | https://github.com/hacan359/xerabora/blob/98949c0efba151f16b234ba5b392b5241791f40e/client/src/snapshot.c | Remontagem, sequência e rejeição |
| S17 | https://github.com/hacan359/xerabora/blob/98949c0efba151f16b234ba5b392b5241791f40e/client/LICENSE | MIT do cliente |
| S18 | https://github.com/RetroAchievements/rcheevos/blob/1433173220a7eaede6a9ed7a18e94117be1821e0/src/rcheevos/consoleinfo.c | Mapas DS/DSi e janela DTCM |
| S19 | https://github.com/RetroAchievements/rcheevos/blob/1433173220a7eaede6a9ed7a18e94117be1821e0/src/rhash/hash_rom.c | Hash DS, função a partir da linha 397 |
| S20 | https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration | Login, callbacks, sessão e User-Agent |
| S21 | https://docs.retroachievements.org/general/hardcore-compliance-requirements.html | Requisitos e aprovação |
| S22 | https://github.com/devkitPro/libnds/releases | Mudanças libnds 2.x/Calico |
| S23 | https://github.com/devkitPro/libnds/blob/v1.8.0/include/nds/timers.h | cpuStartTiming/cpuEndTiming |
| S24 | https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/.github/workflows/release.yml | Toolchains distintas por componente |
| S25 | https://github.com/RetroAchievements/rcheevos/blob/1433173220a7eaede6a9ed7a18e94117be1821e0/LICENSE | MIT, corrigindo referência GPL do fork |
| S26 | https://devkitpro.org/wiki/Getting_Started | Entrada oficial; acesso web retornou 403 |

## Dependências observadas no dscheevos
external/nds-bootstrap: af351f096dd71a37e0e5b18d9709bcc0fb70342f
external/rcheevos: 754965ef28db22b0411bfccbde39154cd09e6b79
external/mbedtls: 068ff080b369adfac81509f9b57b2afabaf82dc5
external/lwip: 77dcd25a72509eb83f72b033d219b1d40cd8eb95
external/nds-bootloader: a0f819008a63f28c4994e7cc8a8ace892450bbb5
tools/melonDS: 8a63c88333c8cb4efed76d866872fc3b6ed0de96

Seu workflow usa devkitpro/devkitarm:20241104 para bootstrap/módulo,
:20260610 para loader e BlocksDS slim-v1.24.0 para launcher.
Essa mistura não é uma recomendação para instalar todas no computador.
O diagnóstico independente escolhe somente a toolchain clássica inicial.

## Reuso
Nenhum código de leitura/hook dos forks foi incorporado. As arquiteturas
foram estudadas, e os nossos fontes foram escritos separadamente.
Uma integração futura baseada em bootstrap seguirá GPL-3.0 e terá notices
por componente. rcheevos oficial é MIT. Não presumir que arte ou submódulos
usem a mesma licença do cliente principal.
