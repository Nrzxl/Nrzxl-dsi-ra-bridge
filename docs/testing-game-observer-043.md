# DSi RA Bridge 0.4.3 — primeiro jogo observado (testes offline)

Estado atual: branch experimental, jogo comercial em DSi físico ainda NOT_RUN.
Jogo-alvo: Super Mario 64 DS Europa, código ASMP, DS/NTR, preflight 042 PASS.

## O que existe

- Fork GPL de DScheevos 59e9978be7b9c3788357ef0a609caf9dc8ea74f3
  e nds-bootstrap af351f096dd71a37e0e5b18d9709bcc0fb70342f.
  Script patch-offline-retail-043.py aplica mudanças apenas a checkouts
  temporários com hashes exatos.
- Caminhos dedicados: sd:/DSiRABridge_043/bootstrap.ini,
  sd:/DSiRABridge_043/dscheevos/session.bin, ROM e save exclusivos.
- O bootstrap ARM9, bootloader ARM7 e módulo ARM9 exigem cada um
  modo SPECTATOR com rede desligada, hardcore desligado. Token fictício
  fixo HANNA_043_LOCAL_FAKE_TOKEN satisfaz a API local, não uma conta RA.
  Não há login de verdade ou envio de achievements oficiais. PMK não é lida.
- O pacote tem conquistas sintéticas locais para 300 e 900 frames
  com leitura DS RAM lógica 0x000000, e uma condição impossível.
  São apenas marcadores QA, não IDs reais RetroAchievements.
- O hash DS da ROM é gerado localmente pela receita pinada do rcheevos,
  validada em CI contra implementação C oficial. Não é SHA256.
- O script prepare-offline-game-043.py exige a ROM ASMP local, relatório
  042 que prove SHA256 idêntico, os dois binários 043 e manifest de build;
  recusa sobrescrita de pasta existente, cria apenas staging novo.

## Como testar no hardware SEM ALTERAR SD PRINCIPAL

1. Preserve o cartão SD atual com Flipnote Lenny e HBMenu intacto.
2. Use OUTRO cartão SD, clonado localmente do atual, incluindo os dados
   do Flipnote e o arquivo de inicialização do HBMenu. O cartão original
   não deve ser usado para o teste 043.
3. Baixe o artefato 043 completo (BINARIES/Bootstrap_043.nds,
   BINARIES/dscheevos9.bin, build-manifest-043.json, script).
4. No PowerShell Windows 5.1, em uma pasta com os arquivos extraídos:

   py -3 .\prepare-offline-game-043.py --rom "C:\Jogos\SuperMario64DS_Europe.nds" --preflight "$env:USERPROFILE\Downloads\DSi_042_Teste_20261119_172248.json" --bootstrap ".\BINARIES\Bootstrap_043.nds" --module ".\BINARIES\dscheevos9.bin" --manifest ".\build-manifest-043.json" --out "$env:USERPROFILE\Downloads\DSi_RA_043_STAGE"

   A pasta do argumento --out deve ser nova e ficar sob o perfil
   Windows. O script não escreve em cartão SD nem cria arquivos em _nds.
5. No cartão RESERVA, copie o conteúdo de STAGE/SD_ROOT/ para a raiz.
   O nds-bootstrap pode escrever scratch/pagefile e _nds no cartão TESTE;
   por isso não é suficiente criar uma pasta no cartão original.
6. Inicie Flipnote Lenny -> HBMenu -> DSiRABridge_043/Bootstrap_043.nds.
   Se Mario iniciar, verifique áudio, botões e save temporário.
   Tente L + DOWN + SELECT para abrir o menu de achievements, e procure
   os indicadores locais QA de 300/900 frames e frames dropped.
7. Se travar, desligue, preserve o cartão RESERVA para análise de logs e
   volte ao cartão ORIGINAL para rollback. Não force gravação no principal.

## Limites técnicos

- 0.4.1 PHYSICAL PASS era para segundo homebrew instrumentado e Wi-Fi;
  043 passa a usar hooks ARM7 VBlank/ARM9 NitroSDK OS_Halt e RAM reservada
  na 0x02D80000..0x02F80000. Wi-Fi 041 NÃO funciona durante o jogo 043;
  o receiver Windows 18217 não receberá snapshots desse teste.
- Mesmo com BINARIES compilados, hardware 043 continua NOT_RUN até
  verificação real do DSi XL; libnds, SDIO, SCFG/MBK e MPU podem bloquear
  a execução pelo Flipnote Lenny.
- Sessão offline sintética é uso único (session.bin -> session.used),
  sem prazo por causa da cópia física ao SD reserva. Depois de um boot,
  para repetir é necessário restaurar nova sessão no SD de testes.
- Nenhuma conquista oficial, sessão RA, login, token ou submissão.
- Nenhum Unlaunch ou alteração de NAND, boot.nds e arquivos _nds do
  cartão original. Não copiar artefatos 042 DO_NOT_INSTALL.
- Ferramentas HANNA são MIT; adaptações DScheevos/nds-bootstrap GPL-3.0,
  com correspondentes fontes pinadas, patches e build no workflow CI.

Fontes:
https://github.com/skierrz/dscheevos/tree/59e9978be7b9c3788357ef0a609caf9dc8ea74f3
https://github.com/skierrz/nds-bootstrap/tree/af351f096dd71a37e0e5b18d9709bcc0fb70342f
https://github.com/skierrz/rcheevos/tree/754965ef28db22b0411bfccbde39154cd09e6b79
