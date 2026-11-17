# Auditoria 0.3.0 → 0.3.1
Data:17/11/2026. Base exata:9c4dd0d9d15c46354b29fa792eefe3087aa6f9f1.
Branch separada:fix/dsi-ra-bridge-network-stability-031. A030 foi preservada.

## Evidências e limites
O arquivo DSi_RA_Bridge_030_Result.json foi lido integralmente: uma sessão
source1/mode1,600 snapshots,9.971211647Hz,RTT4.4227ms,71 duplicatas,
13malformed,CRC0,fora de ordem0,missing0,producerDropped0,engineDropped0.
Há dois eventos LOCAL_TEST_TRIGGER (IDs1/2),submitted:false.
O relato do usuário de execução pelo Flipnote/HBMenu é evidência manual
de hardware030; provenance no JSON permanece RUNTIME_UNVERIFIED.
O JSON não contém os bytes/seq/instantes das71 ocorrências ou das13falhas.

NET000.drb identificado foi preparado para revalidação, mas a importação
local falhou no helper oficial com AttributeError:os.setxattr indisponível
no Windows. Nenhum arquivo binário ficou acessível no destino.
Logo **BLOCKED** a revalidação binária nesta execução; NÃO repetir como
PASS o resumo anterior de CRC/frames. O validador reproduzível é entregue.
O JSONL indicado em C:\DSi_RA_Bridge_Receiver_030\logs-030\... não existe
neste ambiente (**BLOCKED**); não foi inventado ou reconstruído.
Não publicar JSON privado ou log do usuário no GitHub.

## Defeitos confirmados por código e regressão
1. Receiver030 só aceitava DSO3 se correspondia ao único pending atual.
   PONG repetido após o primeiro limpar pending, ou atrasado após um novo
   ping, incrementava malformed. Não havia diagnóstico por causa.
   031 retém32 desafios, marca resposta consumida e distingue repetição,
   resposta tardia e nonce desconhecido. RTT só é medido uma vez/desafio.
   Regressão injeta resposta dupla no Core de produção e no UDP real do CI.
   Isso demonstra o defeito de classificação; NÃO prova que as13 ocorrências
   históricas foram esse caso.
2. Seq duplicada era contada, sem bytes/assinatura nem horário nos logs.
   031 registra seq/frame/comprimento/SHA256 e igualdade de conteúdo,
   distingue conflito, mantém janela limitada e nunca reavalia duplicatas.
3. Frequência030 usava frame % (60/rate): para17Hz enviava~20Hz nominal.
   031 usa acumulador racional de fase;10Hz mantém intervalo nominal6frames.
   Não equivale a captura porVBlank num monitor de jogos.
4. udp.send do receiver não tinha callback para erro por envio.
   Agora conta falhas e não encerra por erros UDP transitórios selecionados.
   Erros de socket fatais continuam encerrando; testes de falha usam injeção
   explícita no transporte de produção (não teste de desconexão física).
5. Descartes por backpressure do motor não tinham evento individual.
   Limite4096B passa a considerar a linha nova, contando descarte visível.
6. Inicialização Windows podia depender da política PowerShell.
   Novo .cmd chama Node direto; não altera configuração persistente.

## O que NÃO foi estabelecido
A aplicação030 não implementa ACK/retry de snapshot. O ARM9 produz uma
vez por seq; a fila única é consumida/limpa dentro de irqLock, antes de
sendto; falha de envio não repõe o pacote. O ARM7 é o default do SDK.
HELLO periódico e PONG são20B, não passam por Sequence.push de64B.
Portanto os71 aumentos no contador significam snapshots já vistos pelo
receiver; não são uma simples contagem de HELLO como snapshot.
Não há evidência suficiente para escolher entre duplicação abaixo da
aplicação (SDK/driver/rede), envio repetido não observado no cenário,
outro produtor ou outra condição. Não culpamos rádio/roteador.

031 não "corrige71" por esconder duplicatas ou trocar Wi-Fi.
O mesmo driver/SDK, perfis, associação e fechamento foram preservados.
O queue helper C utilizado no NDS também é compilado/testado no host:
1800 produções, falha de send e buffer cheio, sem retry implícito.
A exportação JSON do transmissor mostra tentativas/sucessos/falhas porseq
(0=não tentado,1=sendto aceitou,2=sendto falhou). Os totais de controles
permitem separar problemas de dados de problemas de RTT.
sendto aceito não prova entrega e não conta retransmissões MAC do rádio.

## Protocolo e compatibilidade
Snapshots DSRBv1,64B,CRC e controles DSH3/DSA3/DSP3/DSO3v1,20B,
não mudaram. O nonce do HELLO031 é0xD5310100|configuredHz (1..30);
é identificação opcional versão031, não autenticação. Receiver030 já
ecoava qualquer nonce e o031 aceita o nonce legado030 sem interpretá-lo.
Não há tipo de controle novo que o030 classificaria como inválido.
Compatibilidade de bytes é testada; matriz cruzada em hardware **NOT_RUN**.

Causas wire:INVALID_CRC,INVALID_LENGTH,INVALID_HEADER,UNKNOWN_CONTROL,
INVALID_VALUE. Causas de estado:UNEXPECTED_CONTROL_STATE,
UNREGISTERED_SESSION,LATE_PACKET. Dados:DUPLICATE_SNAPSHOT,
CONFLICTING_SNAPSHOT,SEQUENCE_DISCONTINUITY. Limites:CAPACITY_DROPPED,
RATE_DROPPED. Sem erro CRC e com erroheader é possível; classificação
prioriza validação deheader antes deCRC, exceto controles desconhecidos
com header válido, cujoCRC é validado antes deUNKNOWN_CONTROL.

HELLO repetido atualiza heartbeat. PONG repetido conhecido não renova
a sessão nem mede RTT de novo. Após3.5s sem atividade, snapshot não
ressuscita sozinho: exigeHELLO. MesmoHELLO não zera Sequence/motor;
reset de coleta exige nova sessãoY. Reordenados contam recuperação de
perda dentro da janela, mas não são avaliados tardiamente no motor.

## Validação
Scripts antigos protocol632/client7/nds29/live31 continuam.
Nova suíte Core exercita600+1200 snapshots,duplicação,conflito,reordenação,
32bitwrap,timeout/HELLO,nonce errado,reset de sessão,CRC,truncamento,
limites,taxa,erro deenvio e backpressure. OCore é o mesmo do receiver.
Novo teste entre processos transmite600+1200 por UDPloopback com
simuladores identificados,mais falhas controladas,exportaJSON/JSONL e
encerra receptor com sessão ativa. Compila/avalia rcheevos real local.
O Actions é a fonte dos resultados de execução; artefatos guardam logs,
manifestos,ELF/mapa,NDS e validação estrutural. Não preencher PASS de
hardware com sucesso desses testes.

**NOT_RUN**:hardware031,WPA2/SDIO031,estabilidade prolongada real,
câmera (não usada),jogo coexistente,monitor entreprogramas,conquistas oficiais.
Semcredenciais,semNAND,semloader experimental distribuído nesta etapa.

Histórico de validação: o primeiro CI passou em Linux/ARM, mas o teste de
1.200 snapshots no Windows ultrapassou o deadline de 30s. O transporte
continuava recebendo no ensaio local (600 + 1.144 registros no instante
do encerramento). O deadline do teste foi ampliado para 60s para tolerar
a resolução de timers e escalonamento do Windows. Não é correção de rádio.
O resultado final deve ser verificado no run do commit posterior.
