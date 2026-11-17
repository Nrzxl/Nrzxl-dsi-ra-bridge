# Monitor persistente: experimento separado, ainda NOT_RUN
O Network 030 contém um produtor cooperativo no mesmo homebrew. Nenhuma
instrução do nds-bootstrap ou de um jogo comercial é alterada.
Receber seus dados no Windows não demonstra persistência entre programas.

A rota retail do nds-bootstrap possui CE7/CE9 e pontos de interrupção.
dscheevos é referência para reserva de RAM extra e OS_Halt; a RAM usada
pelo cache de ROM não pode ser tratada como espaço livre universal.
O caminho homebrew/hb não instala automaticamente esses hooks retail.

Próximo gate: fork separado, imagem reservada em linker/map, stack própria,
registro de VBlank, leitura coerente no ARM9 e tratamento explícito de DTCM,
cache, reset e falta de idle. Não inserir rede pesada ou escrita de SD em IRQ.
Um teste A/B precisa comparar áudio, input, frames e saves em cópias isoladas.
O R4 em modo DS não garante os recursos do caminho interno TWL.

O mapa RA DS usa 4 MiB principais em offsets lógicos 0–0x3FFFFF e uma
janela DTCM em 0x1000000–0x1003FFF. A base física DTCM é relocável.
DSi tem outro mapa para RAM extra. Não desreferenciar a janela lógica
0x0E000000 no console. Cadeias de ponteiro devem usar valores do mesmo
frame; endereço ausente não pode virar zero como valor legítimo.

Antes de integrar serviços oficiais: hash DS por rc_hash (não MD5 inteiro),
identificação da ROM realmente executada, callback de memória completo,
avaliação por frame, sessão rc_client, HTTPS, token protegido e User-Agent
próprio. Simulação, replay e memória de teste continuarão excluídos do
caminho de award. Aprovação hardcore exige processo RA separado.

Nenhuma mudança do loader estável foi feita. A ausência de uma PoC retail
nesta fase é deliberadamente registrada: ela depende de validar primeiro
rede no hardware e de uma integração de loader com reservas comprovadas.
