# Protocolo confiável experimental v2 (0.3.2)
Todos os inteiros são little endian. Não há autenticação criptográfica.
O receiver032 aceita v1 de020/030/031; o app032 exige receiver032.
Não se tenta negociar v2 silenciosamente com receiver031.

## Envelope fixo de96bytes
|Offset|Campo|
|---|---|
|0..3|ASCII DSR2|
|4|Versão2|
|5|Tipo: DATA1, HELLO2, ACK3, STATUS4, FIN5, FINACK6, PING7, PONG8|
|6|Origem1 runtime não autenticado;2 simulado|
|7|bit0 retransmissão;bit1 modoDSi;demais bits zero|
|8,12|sessionLo e sessionHi; identificador64bits|
|16|Sequência32bits ou nonce dePING|
|20,24|Argumentos a,b específicos do tipo|
|28..91|Payload64bytes|
|92..95|CRC32 dos primeiros92bytes|

DATA: a=tentativa1..6, b=instante de captura em ms no relógio do produtor.
Payload é exatamente um snapshot DSRBv1; seq,source,mode e sessionLo devem
coincidir com o envelope. A captura DRB no SD continua sendo v1/64bytes.
Tentativa1 tem flagretry0; tentativas2..6 têm flagretry1. Duplicação abaixo
da aplicação mantém flag/tentativa, enquanto o retry da aplicação é rastreável.

HELLO: seq inicial (zero noNDS), a=Hz1..30, b=limite de captura1..6000.
NDS032 tem limite600. Host piloto testa600/1200/6000.
SessãoNDS combinaRTC e ticks/input; não é um UUID criptográfico. Receiver
recusa reutilizarID encerrado. Reiniciar com nova sessão evita confundir
capturas. Não existe prova de identidade física apenas pelo cabeçalho.

ACK: seq=primeiro frame ainda não consumido em ordem; a=bitmap32 de
seq..seq+31 já recebidos; b=créditos livres0..32. ACK cumulativo significa
que o motor devolveu seu recibo de avaliação. Em modo explicitamente sem
engine, significa consumo ordenado de transporte e evaluated permanece0.
Bitmap significa apenas recebido/retido; não significa avaliado.
O sender pode evitar retries de bitsSACK, mas só descarta cache após ACK
cumulativo. O receiver retém no máximo32 frames incluindo o in-flight.

O envio original e o retry usam o mesmo payload de captura. SHA256 do
payload identifica repetição idêntica; conteúdo diferente para mesma
sessão/seq falha fechado. Janela histórica1025; pacotes mais antigos são
rejeitados sem avaliação. Sequência usa aritmética modular com janela<2^31.
Nada pode criar um frame zero fictício para preencher uma lacuna.

RTO: começa300ms, SRTT/RTTVAR inteiros, intervalo100..2000ms.
Karn exclui amostras retransmitidas da estimativa. Até6 tentativas por
snapshot; backoff exponencial limitado2s. Budget esgotado é falha visível.
Crédito0 impede novos envios; fila32 cheia pausa a captura controlada,
registrando backpressure. Isso é aceitável neste probe; NÃO é solução para
descartar frames de um jogo real.

STATUS: seq=nextProduced, a=estado(1ativo,2drenando,3falha,4drenado),
b=alvo;16uint32 no payload:
captured,queued,originalAttempts,originalAccepted,sendFailed,retryAttempts,
retryAccepted,acked,unacked,queuePeak,backpressure,exhausted,ackRx,
ackDuplicate,rtoMs,captureToAckMaxMs.
STATUS pode se perder; JSON exportado do console é a evidência final do sender.

FIN: seq=final exclusivo. FINACK só é emitido se next==final, sem buffer,
sem frame em voo e sem falha. FIN repetido recebeFINACK de novo, sem
reavaliar. NDS tentaFIN até6vezes; B pede drenagem com prazo8s. START
aborta; falha de rádio encerra retendo os contadores de não confirmados.
Sem progresso deACK por15s também falha. Receiver expira sessão inativa
por15s, guardando diagnóstico; retomada não reconstitui estado perdido.
Reinício do receiver exige nova coleta/sessão, não replay em sessão oficial.

## Tempo e ordem
Captura, transporte, retenção e avaliação têm contadores distintos.
Cada avaliação é serial e usa o próximo número esperado; recuperação de
seq66/555 desbloqueia a ordem, nunca insere a amostra depois do frame
seguinte já ter sido avaliado.
O recibo LOCAL_TEST_PROGRESS vem depois de rc_runtime_do_frame.
Os IDs1/2 são locais, submitted:false.

Relógios DSi/PC não são sincronizados. O PC mede recepção→avaliação e RTT
com desafio, além de jitter das amostrasRTT. Não mede captura→avaliação
absoluta. captureToAckMaxMs no próprio console é limite superior que inclui
a respostaACK depois da avaliação, não latência de ida.
Captura10Hz ainda não serve a todas as condiçõesRA dependentes de frames.
