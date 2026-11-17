# Monitor persistente: próximo marco, ainda NOT_RUN

A 0.3.1 lê quatro valores controlados do próprio aplicativo. Seu worker,
ARM7 e Wi-Fi não foram demonstrados após carregar outro programa NDS.
A próxima prova deve usar dois programas próprios, primeiro sem rede.

## Fontes e diferenças relevantes

Fontes primárias inspecionadas em 17/11/2026:

- [nds-bootstrap f6728b](https://github.com/DS-Homebrew/nds-bootstrap/tree/f6728baaa28a6fffbd070badce60d0b470180e1e):
  retail/bootloader/source/arm7/hook_arm9.c encontra tabelas de IRQ
  por assinaturas em hookNdsRetailArm9. Há cardengines ARM7/ARM9 e
  variantes DSi. hb/bootloader/source/arm7/hook.c possui lógica própria
  para o dispatcher homebrew. Um hook NitroSDK não serve automaticamente
  ao Calico moderno.
- [DScheevos 59e9978](https://github.com/skierrz/dscheevos/tree/59e9978be7b9c3788357ef0a609caf9dc8ea74f3):
  README, docs/architecture.md, docs/hardware-access.md, module/src/module.c,
  module/module.ld e core/src/dscheevos.c foram lidos. O projeto declara
  WIP, não aprovado pelo RA e sem teste físico DSi do próprio projeto.
  Isso não invalida o transporte físico independente que o usuário testou
  com DSi RA Bridge 030.
- A arquitetura atual do DScheevos usa CE7 para contar VBlanks e OS_Halt
  no idle ARM9 para captura, avaliação e rede, com stack própria.
  Não é simplesmente executar rcheevos inteiro dentro de VBlank.
  Há fallback com leitura live de alguns ponteiros e repetição de snapshot
  em frames sem idle: essas diferenças semânticas exigem auditoria.
- O linker e a arquitetura reservam 2 MiB em 0x02D80000–0x02F80000,
  retirados do cache de ROM do fork. Não são RAM livre universal.
  Código e dados têm aliases, cache e permissões MPU específicos.
- Seu shim ARM7 para SDIO é diferente do default Calico do nosso probe.
  A documentação relata evitar SDIO durante leitura SD e suspender rede
  quando o jogo usa rádio DS. Reutilizar só o nosso worker quebraria a
  integração de áudio, FIFO, IRQ e operações do cardengine.
- O caminho homebrew usa BIOS wait e tem startup próprio. Não oferece
  automaticamente OS_Halt e os hooks usados por jogos NitroSDK.

## Escolha para a próxima prova

| Rota | Benefício | Bloqueio | Decisão |
|---|---|---|---|
| Launcher e payload próprios, ABI residente explícito | Mapas e startup sob nosso controle | Ambos devem preservar RAM, IRQ e ARM7 | Primeira PoC, offline |
| Fork DScheevos/nds-bootstrap retail | Infraestrutura de reserva e hooks já existe | GPL, ABI extenso, rede diferente e validação física pendente | Referência para etapa posterior |
| Substituir ARM7 do jogo pelo Calico do probe | Reuso aparente do transporte | Pode destruir áudio, FIFO e SD | Não implementar dessa maneira |
| Executar diagnóstico antes/depois do jogo | Simples e removível | Não lê memória durante o jogo | Insuficiente para conquistas |

O launcher experimental, o payload homebrew e a imagem residente precisam
ter uma convenção documentada de segmentos. Os linkers de ambos devem
excluir agente, stack, ring e header ABI; comparar todos os intervalos ELF
antes do boot. Usar guards e recusar sobreposição. Um loader genérico pode
limpar RAM, reiniciar ARM7 ou trocar IRQ: por isso ainda não foi distribuído
um segundo NDS com promessa de persistência.

ABI proposto: attach/detach, contador de frames, reset epoch, cancelamento,
allowlist de leituras e callbacks com custo limitado. Primeiro coletar
contador, ponteiro e alvo atualizados pelo segundo programa. A prova deve
mostrar que código e stack residentes ficam fora dos segmentos do payload.
Nada deve substituir _nds/, boot.nds, TWiLight ou nds-bootstrap estáveis.

Gates de engenharia:

1. Capturar 6.000 frames ordenados entre os dois programas. Exercitar DTCM
   relocável, cache sujo, reset, falta de idle, overflow e troca de IRQ.
2. Comparar áudio, input e tempo de frame A/B com e sem agente.
3. Só então anexar rede e demonstrar coexistência de SDIO, SD e áudio.
4. Depois estudar o caminho retail num fork separado, com jogos próprios.

## Captura por frame não é envio a 10 Hz

Condições com hits, delta/prior e ponteiros transitórios precisam de cada
frame lógico. Não se pode descartar cinco em seis frames e chamar isso
uma implementação fiel. Captura e envio terão frequências independentes.
Um envelope futuro pode agrupar seis frames, mantendo cada snapshot
individual e a ordem; isso exige outro formato versionado.

Orçamento calculado, ainda não medido no DSi com agente persistente:

| Operação | Custo calculado |
|---|---|
| 16 bytes observados × 60 frames/s | 960 bytes/s de leitura útil |
| Snapshot wire 64 B × 60/s | 3.840 bytes/s de payload |
| Um UDP IPv4 por snapshot, +28 B | 5.520 bytes/s, sem Wi-Fi e retransmissões |
| 4.096 bytes observados × 60/s | 245.760 bytes/s de leitura útil |
| Ring de 128 snapshots × 64 B | 8.192 B, cerca de 2,13 s |

A meta inicial da PoC será menos de 0,5 ms de trabalho ARM9 por frame,
medindo mediana, p95 e pior caso; é meta, não resultado. Frames perdidos
devem ser zero no fixture controlado. O probe atual possui buffer 38.400 B,
stack de worker 32.768 B e agora 600 B de resultados de envio, além do SDK.
ELF, mapa e size reais acompanham o artefato para calcular a ocupação total.

DTCM deve ser lida pelo ARM9; sua base é relocável e deve vir do contexto
CP15 efetivo. Endereços RA são lógicos, não ponteiros físicos diretos.
O cache ARM9 impede tratar uma cópia ARM7 de RAM como visão coerente.
Limpar cache global a cada frame pode prejudicar o jogo.

Capturar allowlist e todos os alvos de ponteiro no mesmo epoch. Se houver
mutação durante a captura, invalidar o frame; ausência não pode virar zero
legítimo. Mascarar IRQ não impede todos os produtores DMA. No homebrew
próprio é possível implementar publicação cooperativa e guards; isso não
prova coerência de um jogo retail arbitrário.

Overlays, heap, stack, cache de ROM e DTCM exigem intervalos de exclusão.
Reset precisa cancelar filas e limpar estado de avaliação. Jogos sem
OS_Halt ou sem tempo idle suficiente podem precisar ser marcados
unsupported. Não mover avaliação pesada para VBlank como solução geral.

## Integração oficial e licenças

O engine 031 permanece no rcheevos oficial
1433173220a7eaede6a9ed7a18e94117be1821e0 (MIT), com condições locais.
Não há rc_client, login, HTTP ou award. IDs 1/2 não são IDs de conquistas RA.

Para o marco oficial: rc_hash DS sobre a ROM realmente executada, callback
de memória RAM/DTCM correto, captura por frame validada, rc_client, HTTPS,
User-Agent próprio, autenticação e token protegido no Windows.
Rever a política vigente de integração e hardcore com RA antes de habilitar
envios. Simulação e replay devem permanecer excluídos do caminho de award.

nds-bootstrap e DScheevos são GPL-3.0. Seu código não foi copiado para o
Core MIT da 031. Um fork distribuído exigirá licença, fontes correspondentes
e avisos das dependências. Nesta fase há pesquisa e plano; não há loader
persistente novo validado ou instalado.
