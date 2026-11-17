# DSRB diagnostic v1
64 bytes, little-endian; um registro por captura. Não é xeRAbora RA15.
Não possui autenticação, identificação RA de jogo ou capacidade de award.

| Offset | Bytes | Campo |
|---|---:|---|
| 0 | 4 | ASCII DSRB |
| 4 | 1 | versão 1 |
| 5 | 1 | origem: 1 runtime controlado não verificado; 2 simulação |
| 6 | 1 | modo: 0 DS; 1 DSi |
| 7 | 1 | flags: exatamente 1, diagnóstico controlado |
| 8 | 4 | session, identificador local sem valor de segurança |
| 12 | 4 | seq, sequência de captura |
| 16 | 4 | frame, iteração do laço da aplicação |
| 20 | 4 | readTicks, leitura de 16 B medida pelo libnds |
| 24 | 4 | producerDropped, 0 no espécime atual |
| 28 | 2 | tamanho do cabeçalho 44 |
| 30 | 2 | número de palavras 4 |
| 32 | 2 | tamanho de payload 16 |
| 34 | 2 | reservado 0 |
| 36 | 4 | watchlist fixa 0xD1A60001 |
| 40 | 4 | endereço informativo do buffer próprio; não desreferenciar no PC |
| 44 | 4 | palavra 0: 0x44534931 |
| 48 | 4 | palavra 1: contador |
| 52 | 4 | palavra 2: botões, limite 0x3FFF |
| 56 | 4 | palavra 3: contador XOR botões XOR 0xA5A55A5A |
| 60 | 4 | CRC32 IEEE sobre os 60 bytes anteriores |

Arquivo .drb é concatenação de registros. Tamanho não múltiplo de 64
indica truncamento. Não truncar silenciosamente nem completar com zeros.
UDP diagnóstico usa um registro por datagrama e porta 18216 por padrão.
DSRB? / DSRB! são consulta/resposta de descoberta de laboratório no
cliente Node; não há agente de Wi-Fi no .nds desta fase.

Taxa de chegada é medida pelo relógio do receptor. Em replay, é taxa
de processamento, não frequência física. Latência unidirecional fica null.
CRC32 não autentica o produtor e dados importados não habilitam RA.
