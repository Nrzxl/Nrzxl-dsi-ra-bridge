# DSi RA Bridge 0.4.2 — caminho para observar jogos Nintendo DS

Data: 19/11/2026. Branch QA isolada, derivada da 0.4.1 PHYSICAL PASS.

## O que mudou

A 0.4.1 provou no DSi XL via Flipnote Lenny → HBMenu que um segundo homebrew
instrumentado externamente e a pilha Wi-Fi padrão podem coexistir:
975 snapshots únicos, 9,91 Hz, 0 CRC e 1.200 registros locais íntegros.
Isso não é monitoramento de títulos comerciais.

A 0.4.2 inicia a rota retail sem perder a base:
1. scripts/retail-preflight-042.py examina localmente o cabeçalho de uma
   cópia própria de jogo NDS, sem modificar ROM, saves, NAND ou SD.
   Identifica segmentos ARM9/ARM7, recusa overlaps diretos com a reserva
   pretendida e bloqueia DSi-enhanced/exclusive até suporte específico.
   Um cabeçalho válido não comprova compatibilidade real.
   Pode validar até 32 endereços lógicos RAM DS/DTCM, mas não lê memória.
   Hash SHA256 opcional NÃO é hash Nintendo DS do RA.
2. scripts/audit-retail-upstream-042.py verifica revisões exatas de
   DScheevos, nds-bootstrap e rcheevos, hook OS_Halt NitroSDK,
   VBlank ARM7, avaliação ARM9 em idle e reserva 2 MiB, identificando
   riscos de firmware, sessão e rede.
3. CI executa core real do DScheevos em host e regressões, sem
   autenticação RA, ROM de usuário ou distribuição de retail NDS bootável.

## Por que não copiar Wifi041 para jogos

O jogo e nds-bootstrap possuem suas próprias IRQ, FIFO, cache de ROM,
e acessos SD, áudio e rede. O processo que carregou o jogo termina.
O hook launcher041 é injetado só numa fixture cooperativa.
O caminho NitroSDK requer reservar memória e integrar cardengines
ARM7/ARM9 sem sobrepor o jogo. A captura precisa preservar cache ARM9,
ponteiros, DTCM e overlays e trabalhar em idle, não em VBlank.

O DScheevos possui essa arquitetura, mas a fonte consultada é WIP
e não validada no DSi físico. O código upstream contém readFirmware
para PMK e wipeSession que altera arquivo de sessão. O launcher
inclui login, HTTPS e a pasta _nds. Nenhum desses caminhos é autorizado
na etapa 042 de auditoria offline. Não inserir ROM/senha no GitHub.

## Gates até observar jogos físicos

Gate A agora: validar as fontes e testar core retail em host; preflight
read-only para cópia própria local.
Gate B: criar um fork GPL totalmente isolado, com rede, autenticação,
leitura PMK e envios RA desligados, e arquivos em pasta distinta.
Testar leitura em jogo NTR NitroSDK de teste antes de distribuir binário.
Gate C: comprovar no DSi físico o contador VBlank e dados ARM9 RAM/DTCM
durante um jogo, mantendo áudio, input e saves intactos. Se as
permissões Lenny não bastarem, marcar BLOCKED, sem Unlaunch/NAND.
Gate D: frames lógicos a 60 Hz sem perdas silenciosas, overlays,
reinício e comparação com rcheevos Windows.
Gate E: integração RA legítima com aprovação e requisitos de segurança.

## Instalação

Não há instalação no DSi nesta entrega. A 0.4.1 permanece intacta.
Nunca copiar o checkout upstream _nds para o SD físico na etapa 042.
O git checkout no CI é apenas auditoria de fontes.

Exemplo PowerShell 5.1 (substitua pelo caminho da sua cópia legítima):
  py -3 scripts/retail-preflight-042.py "C:\Jogos\MeuJogo.nds" --sha256

HEADER_ONLY_PASS_MORE_GATES_REQUIRED não autoriza executar o jogo com
monitor 042. É somente validação de segmentos básicos do cabeçalho.

## Revisões

DScheevos 59e9978be7b9c3788357ef0a609caf9dc8ea74f3 GPL-3.0
nds-bootstrap af351f096dd71a37e0e5b18d9709bcc0fb70342f GPL-3.0
rcheevos 754965ef28db22b0411bfccbde39154cd09e6b79 MIT
0.4.1 validada em qa/dsi-observer-wifi-integration-041-20261119
