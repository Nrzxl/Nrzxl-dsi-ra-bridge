# Próxima etapa de engenharia
| Ordem | Experimento | Critério para avançar |
|---|---|---|
| 1 | Executar build ARM isolado | Dois .nds iguais, logs, ELF/map e notices |
| 2 | Executar o .nds pelo Flipnote Lenny/HBMenu | Mode identificado, 7 checks, Errors=0 |
| 3 | Exportar e reproduzir snapshot | 600 registros íntegros, 38.400 bytes |
| 4 | Medir versão com/sem coleta no homebrew | Custo por frame, eventos perdidos, estabilidade |
| 5 | Criar repo privado separado | HEAD e fontes preservados, sem dados pessoais |
| 6 | Isolar loader experimental no SD | Nenhum path estável substituído |
| 7 | Instrumentar CE9/CE7 com gate de modo | Reserva linkada, hooks preservam ABI e cache |
| 8 | Testar caminho retail corretamente | Homebrew cooperativo não basta como prova |
| 9 | Rádio independente antes de coexistência | Pacotes físicos, RTT, perdas, reconexão |
| 10 | Plano de leitura de sets | Cadeias coerentes, DTCM dinâmico, rejeição explícita |
| 11 | Comparar rcheevos oficial com referência | Triggers, hits, deltas e measured por frame |
| 12 | Consultar RA sobre cliente em hardware | Fluxo e política de integração esclarecidos |
| 13 | Sessão softcore de jogo real | Captura validada desde boot, conta e hash corretos |
| 14 | Overlay e compatibilidade por jogo | Sem corrupção de VRAM, áudio ou save |

A aprovação hardcore exige regras, identidade própria e processo RA.
Os critérios oficiais incluem funcionamento de achievements/RP/leaderboards,
controles de cheats/states/debug e requisitos de histórico público.
Não vamos ligar esse modo enquanto existir edição/replay de snapshots.

Dependem do console: modo/permissões reais da entrada Flipnote Lenny,
FAT do SD interno, retorno ao HBMenu, estabilidade e depois SDIO.
Dependem do ambiente de desenvolvimento: todos os builds, emulador,
pacotes, sockets locais e compilação do demo C.
Dependem de trabalho de implementação ainda não realizado: loader
isolado, monitor retail, rádio, validação de watchlists e cliente RA.
