# Testes e interpretação
Siga docs/build.md antes de docs/sd-test.txt.

| Teste | Evidência esperada | Executado aqui |
|---|---|---|
| CRC conhecido | 0xCBF43926 para bytes ASCII 123456789 | PASS em JavaScript |
| Limites offset/tamanho | Rejeição de overflow e leituras fora do objeto | PASS em JavaScript |
| Pacotes | Rejeitar tamanho, versão, flags, CRC e layout inválidos | PASS em JavaScript |
| Sequência | Detectar falta, duplicação, fora de ordem e wrap | PASS em JavaScript |
| 600 snapshots | Decode/encode e valores preservados | PASS em JavaScript |
| Memória real da aplicação C | 7 checks, erros zero, 600 amostras | NOT_RUN |
| Dois builds ARM | .nds idênticos + digest/pacotes registrados | BLOCKED |
| Emulador | Boot e exportação do mesmo .nds | NOT_RUN |
| Node/Python no Windows | Replay com labels corretos | NOT_RUN |
| UDP entre processos | 120 pacotes simulados em loopback | NOT_RUN |
| rcheevos C | Dois triggers locais e measured | NOT_RUN |
| DSi físico | Captura devolvida pelo usuário | NOT_RUN |
| Monitor de outro jogo | Hook persiste, frame coerente, A/B | BLOCKED |
| Wi-Fi durante jogo | Pacotes físicos e coexistência SD/rádio | NOT_RUN |
| Conquista oficial | Sessão real + resposta RA | NOT_RUN |

PASS em JavaScript é uma execução real do protocolo, usando V8 de
orquestração. Não é equivalente a GCC, browser, Node, Python, Windows
ou DSi. As 632 verificações incluem 32 checagens e 600 casos de uma
sequência controlada; não são 632 testes independentes de hardware.
Não foram usados ROMs ou credenciais RA.

O primeiro teste falhou porque TextEncoder não existe nesse V8.
O teste foi ajustado para um vetor ASCII literal, sem mudar o CRC de
produção, e a suíte então passou. O histórico não foi ocultado como
se a primeira execução tivesse sido PASS.

Logs de build, hash do binário, snapshot e foto permitem comparar
expectativa com execução. Nenhum deles sozinho certifica cliente RA.

Teste adicional: node tests/client-tests.cjs
Foram executadas aqui 7 verificações de integração unitária do CLI com mocks de filesystem. A simulação gerou 38.400 bytes em memória e o replay validou 600 registros. UDP real continua NOT_RUN.
