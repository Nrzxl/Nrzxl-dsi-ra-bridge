# Viabilidade — avaliação em 16/11/2026
## Conclusão de engenharia
Existe uma rota plausível para conquistas reais em DS no DSi físico usando
instrumentação do carregador. Não há aqui prova de execução dessa rota no
DSi físico do usuário. O bloqueio imediato desta sessão é operacional: o executor
local recusou comandos e gravação de arquivos com “No usable execution
environment is available”. Não foi possível clonar, instalar, compilar ou
rodar emuladores. Os fontes foram inspecionados diretamente pelo GitHub.

A primeira entrega é um pacote de fontes recuperável e testes JavaScript
executados. O .nds compilado e o ZIP pronto para SD permanecem BLOCKED.
Este relatório não substitui os artefatos faltantes nem transforma testes
de computador em compatibilidade de console.

## Arquitetura do console e contexto de execução [S1, S2]
ARM9 executa o jogo e acessa seu DTCM; ARM7 atende periféricos e funções
de sistema. Um aplicativo HBMenu não sobrevive automaticamente ao início
de outro programa. Seria necessário manter código residente dentro do
ambiente preparado pelo loader e reservar memória explicitamente.

DS oferece 4 MiB de RAM principal; DSi tem 16 MiB, mas exposição ao programa
depende do modo, SCFG e do loader. O DTCM do ARM9 tem 16 KiB e endereço
configurável. ARM7 não é leitor transparente do cache ou DTCM do ARM9.
Não deduzir “12 MiB livres” só porque o jogo foi feito para DS: bootstrap,
cache de ROM, buffers e módulos já usam partes dessa RAM.

A identificação isDSiMode() indica o ambiente de execução, não distingue
de forma independente DSi de 3DS em modo TWL. O diagnóstico mostra esse
limite e informa tamanhos esperados, sem varrer RAM extra ou tentar
destravar SCFG.

## dscheevos: principal referência de DSi [S3–S6]
A main observada é 59e9978be7b9c3788357ef0a609caf9dc8ea74f3.
O README declara WIP, sem release pronta, sem aprovação RA e ainda não
experimentado em DSi físico. Portanto, suas medições são resultados
relatados pelo autor em bancada, não validação independente desta entrega.

Há launcher, core, módulo e forks de bootstrap/melonDS. Os submódulos
fixam versões de rcheevos, lwIP, mbedTLS e loader. A main já usa um fork
otimizado de rcheevos; não equivale ao upstream sem alterações.
Branches observadas incluem main, perf, arm7eval, bootstrap-hooks,
live-unlocks, twilight-e2e e wpa2-rekey. A lista e os SHAs consultados
foram preservados em research/dscheevos-branches.json.
Não se deve escolher a branch de nome mais promissor sem comparar código.

O histórico recente trata de equivalência de comportamento e custo:
patches de avaliação, bancada de frames e remoção de leituras de timers
do jogo para entropia. Isso mostra que “não travou” é evidência insuficiente;
áudio, tempo de execução e efeitos indiretos também precisam de comparação.

O projeto documenta reserva de 2 MiB em RAM extra e redução do cache de ROM.
Esse mapa é um exemplo para seu fork, não um endereço livre universal.
A rotina read_memory do módulo distingue RAM DS e janela lógica de DTCM.
Os hooks encontram OS_Halt, redirecionam sua entrada e mantêm contagem de
VBlank. Sem um ponto de trabalho compatível, o módulo deve recusar ativação.

A documentação descreve transporte SDIO no ARM7 e processamento de rede
fora de IRQ. O Wi-Fi de jogo pode conflitar com o monitor; detalhes de
associação, chaves e timing permanecem dependentes de testes físicos.
Não reutilizaremos a parte de credenciais ou dumps no diagnóstico.

## Fork Retroachievements-DS-on-3DS [S7–S9]
HEAD inspecionado: 4d60695487a5593531c0c395e8d4d1ae2ca91fad.
Em retail/cardenginei/arm9/source/ra_reader.c, ra_tick retorna quando
consoleModel == 0. Logo o DSi é deliberadamente excluído desse caminho.

O leitor entrega o snapshot a um binário separado em WRAM após verificar
presença/código. Isso responde onde existe persistência: no cardengine
injetado e no binário reservado, não em um processo HBMenu concorrente.
Overlay e mudanças em interrupções exigem compatibilidade por jogo.

Há inconsistência de atualização: o README ainda diz que ra_client/ra_net
não começaram, mas a árvore contém ra_net.c, ra_queue.c, ra_rcheevos.c e
o histórico posterior relata rede e desbloqueios. A documentação extensa
tem registros de fases antigas. Não tratar a tabela inicial como estado
atual de todos os componentes.

O commit f7dd6bc723c649346bd7fb610363b8f15ade684f relata falha da
associação de rede durante jogo em seu hardware. Esse achado não prova
impossibilidade de rede no DSi, mas impede presumir que preservar a
associação do launcher seja solução pronta.

## nds-bootstrap e TWiLight Menu++ [S10–S13]
O bootstrap carrega títulos nativamente e oferece caminhos diferentes:
retail/cardenginei para jogos com hooks e hb para homebrew. No upstream
foi localizado myIrqHandlerVBlank no cardengine ARM7. O fork de dscheevos
adiciona um ponto OS_Halt, carga do módulo e contrato de cache.
É nessa camada, com reserva e contratos próprios, que um monitor precisa
entrar. Não basta anexar uma biblioteca ao executável do menu.

O TWiLight configura o carregador; sua árvore distingue componentes de
menus e seleção. O histórico recente inclui mudanças na rota de carga.
Como paths de bootstrap são usados pelo menu, “trocar só o arquivo
nightly” também alteraria uma instalação estável. Não faremos isso.
Uma etapa futura precisa de frontend/loader experimental separado ou de
uma cópia de SD dedicada, sem tocar no R4 estável.

Homebrew próprio usa o caminho hb e não prova hooks retail. O espécime
cooperativo desta fase mede leitura e coleta dentro do mesmo aplicativo.
Não o apresentamos como monitor persistente de jogo comercial.

## R4, Flipnote Lenny e firmware [S14]
O R4 SDHC citado é tratado como flashcart em modo DS, sem CPU extra
programável presumida. DLDI dá acesso ao microSD, não cria RAM adicional
nem acesso garantido ao SD interno. B4DS/SCFG bloqueado difere do caminho
DSi pelo SD. O diagnóstico recusa exportação se sd:/ não estiver montado;
não redireciona silenciosamente para fat:/ no R4.

A documentação do DSi Guide aponta Flipnote Lenny como alternativa para
câmera defeituosa e registra a limitação de Slot-1 nesse contexto.
É a entrada apropriada já relatada pelo usuário. Não presumimos acesso
irrestrito a todos os recursos TWL apenas porque o HBMenu abriu.
Não foi confirmado backup NAND. Nenhum passo aqui depende de tê-lo.
DSiWareHax, dslink e fwTool existentes não precisam ser substituídos.

## xeRAbora: o que transferir e o que não transferir [S15–S17]
O protocolo separa identificação por hash, entrega de watchlist e snapshots
UDP. Há proteção contra cópia rasgada, remontagem e detecção de sequência;
cadeias são resolvidas no agente para usar valores de um mesmo frame.
A estrutura de separação é útil como referência de arquitetura.

O DSi exige outro agente: memória, cache, DTCM, periféricos e orçamento
de CPU não correspondem ao PS2. Não foi demonstrada compatibilidade wire
com RA15; DSRB v1 é deliberadamente um protocolo diagnóstico diferente.
Também não reutilizamos comandos de reset ou mensagens de desbloqueio.

## Mapa RetroAchievements e identificação [S18, S19]
No rcheevos master fixado em 1433173220a7eaede6a9ed7a18e94117be1821e0:
- DS lógico 0x0000000–0x03FFFFF: RAM física 0x02000000–0x023FFFFF.
- DS lógico 0x0400000–0x0FFFFFF: intervalo reservado/inativo no mapa DS.
- DSi lógico 0x0000000–0x0FFFFFF: RAM principal de 16 MiB.
- DS/DSi lógico 0x1000000–0x1003FFF: janela de DTCM.
O 0x0E000000 descritivo de DTCM não é destino físico para dereference
no console. É preciso obter a base atual pelo CP15 no ARM9 e considerar
habilitação, MPU, largura da leitura e possíveis mudanças de mapeamento.

O hash DS de RA não é MD5 do arquivo inteiro. hash_rom.c combina partes
do cabeçalho, binários ARM9/ARM7 e banner; trata cabeçalhos adicionais e
padding de homebrew. Usaremos rc_hash oficial, validado contra um cliente
de referência, antes de identificar qualquer dump. Não enviar ROMs.
Nenhuma rotina de hash oficial foi executada nesta sessão.

## Transmitir apenas regiões necessárias
É possível para leituras diretas; para ponteiros não basta mandar os
endereços fixos encontrados no texto das condições. É preciso preservar
operações de AddAddress, máscaras, escalas e ordem de dependência.
Ponteiros devem ser resolvidos com os valores do mesmo snapshot, e
endereços resultantes validados por CPU/região. Recursos ainda não
implementados devem desabilitar o conjunto, nunca usar zero silenciosamente
como se uma leitura ausente fosse um valor legítimo.

Um pedido de endereço ao Windows seguido de nova leitura no DSi pode
misturar frames. O agente precisa de plano de leitura por frame ou de
buffers suficientes para responder sobre o mesmo frame retido.
Capturar só 10 Hz não atende avaliação que exige cada frame; exportar
snapshots no SD é diagnóstico, sem desbloqueios oficiais nesta fase.

## Alternativas
| Arquitetura | RAM/CPU no console | Obstáculo principal | Decisão |
|---|---|---|---|
| rcheevos e HTTPS no DSi | Maior carga | Sets grandes, idle, SDIO, compatibilidade | Rota futura; estudar dscheevos |
| Agente leve + rcheevos no Windows | Menor avaliação local | Wi-Fi coexistente, frames completos, cadeias | Candidata inicial para monitor real |
| Agente + SD + replay Windows | Buffer e escrita controlada | Não é sessão oficial ao vivo | Diagnóstico desta fase |
| HBMenu concorrendo com jogo | Sem isolamento disponível | Aplicativo anterior é substituído | Rejeitada |
| R4 DS como alvo inicial | RAM/periféricos restritos | Sem reserva DSi presumível | Adiado |

## Orçamento inicial proposto, ainda não medido
DSRB usa 64 bytes por snapshot. A 60 capturas/s seriam 3.840 bytes/s de
conteúdo antes de UDP/IP/Wi-Fi. Isso é estimativa de payload, não benchmark
de rádio, latência ou estabilidade. O buffer atual tem 600 registros:
38.400 bytes, aproximadamente dez segundos nominais de coleta.
Código, ARM7 padrão, libfat e tela têm custo adicional ainda sem map file.
Monitor real usará limite explícito de bytes por frame, filas e contadores
de estouro. Não reservar automaticamente os 2 MiB de outro projeto.
