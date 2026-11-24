# DSi RA Bridge 0.4.6 — laboratório de frames no PC (HOST-ONLY)

## Propósito

Fase para preparar uma ponte de RAM sincronizada por **frame** sem usar o DSi
ainda. A 0.4.4 foi aprovada em duas fotos físicas com RAM mudando, mas lê
1.024 bytes a cada ~120 frames: isso **não** basta para avaliar eventos que
duram somente um frame. A 0.4.5 importou metadados de **157** conquistas RA
de Super Mario 64 DS, jogo oficial **9983**, catálogo fingerprint
\`aded444ebb288d2b60ef9f441f8ed44589bb2b4e57c8973b5ae98db6e4196edf\`.
Esse JSON contém MD5 das condições, **não** condições de execução.

A 0.4.6 implementa uma **PoC local, offline e sintética** para testar o desenho
do transporte e a avaliação em \`rcheevos\` pinado. **Nenhum jogo/ROM/DSi
real, patches de conquistas oficiais, conta ou servidores RA são usados.**
A avaliação nativa usa somente *duas condições inventadas* e uma condição
inalcançável para estresse. O objetivo é provar que os componentes de
laboratório se integram, **não** afirmar que conquistas oficiais funcionam
no DSi.

## Arquiteturas sob avaliação

1. **PC como avaliador (candidata A)**: ARM9 captura apenas a *watchlist* de
   endereços solicitados **a cada frame**; transporta frames ordenados ao
   PC; PC chama \`rcheevos/rc_runtime_do_frame\` com os bytes da mesma
   amostra. **Bloquear avaliação** quando houver qualquer frame perdido,
   valor de memória faltante ou mudança inesperada de sessão. Atrasos de
   rede não podem fazer duas amostras do mesmo frame parecerem duas
   observações distintas. Exige sincronização rigorosa e canal confiável.
2. **DSi como avaliador (candidata B)**: ARM9 usa \`rcheevos\` local por frame,
   PC é só transporte de rede e painel. Pode reduzir o problema de latência
   da avaliação, mas eleva uso de CPU/RAM ARM9. Avaliar com benchmarks,
   instrumentação física, áudio e IRQ antes de selecionar.

**Nenhuma dessas arquiteturas é uma integração aprovada pelo RA**.
\`rc_client\` continua sendo o caminho recomendado para login/carregamento/
sessões em um cliente aprovado. O código deste laboratório usa
\`rc_runtime\` sem networking, apenas para uma prova autocontida.

## Protocolo experimental DR46-v1

\`scripts/frame-bridge-046.py\`: sem socket, HTTPS, login ou gravação no
console; apenas codifica, decodifica e testa pacotes em memória/arquivo local.

- Header little-endian: magic \`DR46\` 4B, versão u8 (=1), flags u8 (=0),
  reservado u16 (=0), session 16B não nula, RA hash do jogo 16B,
  sequence u32, frame u32, region_count u16, payload_len u16,
  crc32 u32 sobre \`header_sem_crc + payload\`.
- Até 32 regiões, payload total de até **1024 B**, tamanho máximo de
  frame serializado de 1080 B.
- Cada região: \`bank u8, offset u32, len u16, data[len]\`. Bank 0: DS
  main RAM lógica \`0x000000..0x3FFFFF\` (4 MiB), bank 1: DTCM lógica
  \`0x1000000..0x1003FFF\` (16 KiB). Esta é a visão do RA, não a
  topologia/cache físico de hardware.
- Só aceita segmentos ordenados, sem sobreposição, sem truncamentos;
  segmentos de 1..256 B. Leitura de endereço fora da amostra do mesmo
  frame falha explicitamente — **não reutilizar** bytes de frame anterior.
- Primeira sequência obrigatoriamente 0; todos os seguintes devem
  incrementar sequência **e** frame de exatamente 1. Duplicação, perda,
  reordenação, CRC incorreto, mudança de sessão, tamanho inconsistente,
  versão incompatível, endereços inválidos ou wrap implícito **bloqueiam**
  o receptor até um *novo* teste/sessão explícito.
- **CRC32 detecta corrupção acidental; NÃO autentica nem garante
  privacidade/integridade contra invasores.** Nenhuma autenticação,
  Wi-Fi/TCP/UDP/ARM9, relógio, FEC, retransmissão, enfileiramento real,
  backpressure ou resume é implementada na 0.4.6.
- Tamanho máximo do corpo é limite de QA, **não medição de banda DSi**.
  Em 60 fps seriam até ~65 KiB/s de wire bruto sem overhead do transporte;
  mediremos capacidade real apenas após a PoC de hardware.

## Laboratório — Windows PowerShell 5.1

Na pasta do repositório, com Python 3:

\`\`\`powershell
py -3 .\tests\test-frame-bridge-046.py
py -3 .\scripts\frame-bridge-046.py demo --out "$env:USERPROFILE\Downloads\DSi046_host_synthetic"
py -3 .\scripts\frame-bridge-046.py verify --input "$env:USERPROFILE\Downloads\DSi046_host_synthetic\synthetic-frames-046.bin"
\`\`\`

A geração se recusa a sobrescrever uma pasta já existente. O relatório
\`synthetic-report-046.json\` registra explicitamente
\`capture_on_dsi=false\`, \`official_unlocks_sent=false\` e
\`official_achievement_definitions_used=false\`.

O arquivo \`synthetic-trace-046.csv\` alimenta
\`lab/ra-runtime-smoke-046.c\` com o **mesmo motor C real** do fork
\`skierrz/rcheevos\`, SHA
\`754965ef28db22b0411bfccbde39154cd09e6b79\` (pin previamente
auditado nos builds DScheevos). Ele avalia um "star" em endereço de teste
0x100, "coins" em 0x101 e um predicado inalcançável em 0x102. **Esses
não são endereços Mario nem IDs de conquistas RA**. Também executa
60 mil iterações em CPU host; isso **não** comprova 60 Hz no DSi.

No Linux (ou GitHub Actions), com checkout do pin de rcheevos em
\`upstream/rcheevos\`:

\`\`\`bash
cc -std=c99 -O2 -Iupstream/rcheevos/include \
  lab/ra-runtime-smoke-046.c \
  upstream/rcheevos/src/runtime/*.c upstream/rcheevos/src/util/*.c \
  -lm -o ra-runtime-smoke-046
./ra-runtime-smoke-046 out/046/synthetic-trace-046.csv
\`\`\`

## Gates e resultados a confirmar

| Gate | Critério | Estado inicial |
| --- | --- | --- |
| 046-A | Pares \`encode/decode\` preservam frame, endereços, valores, hash | CI sintética |
| 046-B | CRC inválido, frame perdido, duplicado, endereço indisponível, sessão trocada **bloqueiam** | CI sintética |
| 046-C | Compilar e executar \`rc_runtime\` real do pin, observar dois triggers **sintéticos** | CI sintética |
| 046-D | PowerShell 5.1 + Python 3 executam simulador no Windows | CI sintética |
| 046-E | Coletar frames da RAM física do Mario ASMP EU, com watchdog/IRQ | **NOT_RUN** |
| 046-F | Importar legitimamente as definições executáveis reais do RA 9983 e medir cobertura 157/157 | **NOT_RUN** |
| 046-G | Teste real de perdas, uso de CPU/RAM/áudio, save, reset e Wi-Fi no DSi | **NOT_RUN** |
| 046-H | Autorização e compliance da integração de conta RA | **PENDENTE DA EQUIPE RA** |

**Sem merge, release, APK, mudanças no SD, ROM, NAND ou Unlaunch.**
Preservar 0.4.4 e 0.4.3 para rollback. O bug intermitente de áudio no
menu continua aberto/adiado. Nenhum desbloqueio oficial enviado.

## Referências técnicas

- Documentação oficial: https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration
- \`rc_runtime_do_frame\`: https://github.com/RetroAchievements/rcheevos/wiki/rc_runtime_do_frame
- \`rc_client_set_read_memory_function\`: https://github.com/RetroAchievements/rcheevos/wiki/rc_client_set_read_memory_function
- Pin upstream: https://github.com/skierrz/rcheevos/tree/754965ef28db22b0411bfccbde39154cd09e6b79
