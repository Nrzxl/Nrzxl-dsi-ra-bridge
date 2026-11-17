# Arquitetura experimental 0.3.3
Branch exclusiva derivada de 606659d7313d60e625a739fdf1f9b93032073795. As árvores das versões anteriores são preservadas.

## Por que a thread de A não sobrevive
O nds-bootloader reinicializa ARM7, IRQs, DMA, timers e RAM antes de carregar as seções ARM9/ARM7 de B. O CRT Calico também redefine MPU, caches, IRQs e sua própria tabela de handlers. Preservar apenas um ponteiro ou um módulo de A não garante execução após essa troca. Isso explica por que a PoC cooperativa 032 não atende ao critério.

## Solução limitada que pode ser verificada
B é um .nds completo, compilado separadamente, com entrypoint, CRT e ARM7 padrão. Seu código não chama o monitor. O patcher host aceita apenas a fixture própria, valida cabeçalho, limites e a instrução exata no handler VBlank de B. Uma cópia nova recebe um branch ARM para um interposer externo. O ARM9 ampliado é carregado depois da limpeza do loader; a janela fica fora da imagem original/BSS e do heap limitado de B. O restante do arquivo, inclusive ARM7 e seções TWL, é preservado.

A inicia esse .nds completo com runNdsFile oficial do HBMenu, isolado em GPL-2.0-or-later. A deixa de executar. A presença do observador em B decorre de instrumentação externa e recarga como parte da imagem, não da sobrevivência literal de uma thread de A. Não é uma solução genérica para qualquer .nds.

## Mapa
| Recurso | Intervalo/tamanho |
|---|---|
| Heap/código/dados de B | abaixo de 0x02100000 |
| Janela reservada | 0x02200000–0x02220000, 128 KiB |
| Código e cabeçalho | máximo 4 KiB |
| Estado | 0x02202000, 64 bytes |
| Registros | 0x02203000, 1200 × 32 bytes |
| Pilha privada | 0x0221C000–0x02220000, 16 KiB |
| Export limitado | primeiros 0xD000 bytes da janela |

A cada VBlank: salvar registros e flags; trocar para pilha privada; ler os 20 bytes autorizados de game_state; validar geração par e checksum; gravar registro com CRC32; restaurar pilha/registradores; executar a instrução deslocada e retornar ao handler original de B. Não há SD, rede, locks nem SDK no callback. Os registros param em 1200, mas observação/counters continuam. O IRQ original recebe 64 bytes adicionais de uso temporário da pilha.

O span medido com VCOUNT cobre apenas a leitura, tem resolução grosseira em scanlines e não é benchmark completo de CPU. Watermark de SP é um limite inferior de uso; canário verifica base da pilha. Não inferir compatibilidade ou desempenho de jogos comerciais a partir dessa fixture.

## Compatibilidade e permissões
Usa os primeiros 4 MiB, sem depender de RAM estendida, DSP, SDIO Wi-Fi, Unlaunch ou chaves NAND. O launcher físico exige modo DSi e sd:/ montável e valida tamanho/CRC do B conhecido. O loader executa com os privilégios herdados; não eleva permissões de Flipnote Lenny. A inicialização ARM7/ARM9 e acesso SD herdados precisam de teste físico. O SDK e o exploit podem impor diferenças entre o ambiente atual e o DS/NTR emulado.
A emulação DSi exigiria firmware/BIOS/NAND privados e escrita numa cópia NAND; não foi escolhida nesta fase. Emulação DS com FreeBIOS não exige esses arquivos. R4 normalmente entra em modo DS com DLDI e sem acesso equivalente ao SD interno: fora do caminho físico desta PoC.

## DScheevos e futuro retail
DScheevos usa uma integração própria com nds-bootstrap: cardengines/hooks ARM7/ARM9, chamada por VBlank e trabalho no idle/OS_Halt, módulo reservado, MPU/cache e pilha próprios. Não se torna residente por apenas abrir um segundo homebrew. Reserva de memória e loader são partes do mesmo projeto; é preciso validar as permissões e footprint em cada jogo.
O próximo passo retail deve usar uma variante GPL separada do nds-bootstrap, em arquivos novos e launcher explícito, com ROM legítima somente leitura, saves experimentais separados e nenhum patch na instalação estável. Não aplicar o patcher desta fixture a jogos.

## Caminho oficial
1. Preservar o arquivo original para identificação; o hash RA Nintendo DS não é SHA256/MD5 genérico do arquivo e não deve ser calculado sobre B instrumentado.
2. Usar rc_hash_generate_from_file com RC_CONSOLE_NINTENDO_DS oficial, com algoritmos/versão fixos e resultados de teste. O hash só resolve título/conjunto; não prova execução legítima.
3. Implementar mapa RA: RAM principal DS, ARM7 e DTCM conforme rcheevos/cliente de referência, sem somar cegamente 0x02000000. Capturar ponteiros/dados consistentemente por frame; cache ARM9 e mirrors precisam de tratamento.
4. Definições podem exigir endereços indiretos dinâmicos e delta/prior/hitcount; uma lista estática de endereços não cobre tudo. Perda ou salto de frame exige invalidar/suspender a avaliação, não inventar frames.
5. Windows hospeda rcheevos/rc_client e HTTPS, credenciais somente locais; login/token, identificação, sessão e eventos oficiais precisam de integração e revisão com RetroAchievements. Não usar web API de consulta como atalho para awardachievement.
6. Só habilitar submissão depois de validar execução contínua de jogo real e conformidade do cliente. Este protótipo não faz requisições oficiais, não autentica e não concede conquistas.
