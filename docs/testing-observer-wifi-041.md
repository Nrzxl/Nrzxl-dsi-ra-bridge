# DSi RA Bridge 0.4.1 — observador ARM9 + Wi-Fi no segundo homebrew

**AVISO:** CI/emulação não validam o rádio no DSi físico desta versão.
É uma prova de integração com nosso segundo homebrew controlado, não um
monitor universal de jogos Nintendo DS nem um cliente de conquistas oficiais.

## Arquitetura

- Da 030 que já transmitiu dados controlados no DSi XL real: devkitARM,
  libnds/Calico, ARM7 padrão do SDK, Wifi_InitDefault(INIT_ONLY),
  wfcLoadFromNvram, wfcBeginAutoConnect, UDP e protocolo DSRBv1/DSH3.
- Da 033 validada fisicamente em 040: Launcher A → segundo NDS B,
  instrumentado por um hook ARM9 externo em VBlank; memória 0x02200000
  e exportação delimitada de 53.248 bytes, OBSnnn.bin. O launcher usa
  componentes HBMenu GPL com fontes fornecidas.
- Alteração 041: o hook externo mantém um latch da última leitura em
  ObserverState.reserved, protegido por sequência par/ímpar. O aplicativo
  B lê somente esses dados etiquetados e os envia a até 10 Hz usando o
  transporte 030. A captura fixa 1.200 permanece idêntica ao formato 033
  e compatível com o decodificador 033.
- O observador **não** usa SDK, SD ou Wi-Fi no contexto de interrupção.
  O transmissor cooperativo está instalado **dentro do segundo homebrew
  de teste**, não num residente universal que sobreviva a qualquer jogo.
- Formato de rede é DSRBv1 original: words[0]=DSI1, words[1]=contador
  observado, words[2]=botões observados, words[3]=checksum controlado;
  frame é o contador do hook. O campo source=1 é RUNTIME_UNVERIFIED
  até confirmação manual de execução real. Nenhum dado de jogo retail.

## Segurança

A rede só inicia com botão Y e apenas se a janela DSIOBS33 e cabeçalho
estiverem íntegros. O arquivo sd:/DSiRABridge_041/receiver.cfg informa
somente IP privado do PC, porta 18216 e taxa fixa 10 Hz. O programa lê
perfis de rede existentes do DSi; não grava credenciais nem diminui a
segurança do roteador. Nunca inicializa Wi-Fi no arquivo de controle
não instrumentado. Não substitui ARM7 nem inclui Wifi_TWL_Update
custom do BlocksDS. O receiver não inicia o motor rcheevos no teste 041.

## Uma rodada física, sem alterar o desbloqueio

1. Com o DSi XL desligado, confira o backup do SD interno. Baixe os ZIPs
   da CI aprovada. Extraia DSi_RA_Bridge_SD_041_HARDWARE_NOT_RUN.zip e
   copie **apenas as novas pastas** nds/DSiRABridge_041 e
   DSiRABridge_041 à raiz do SD, sem sobrescrever arquivos existentes.
   Não tocar boot.nds, private/, _nds/, R4, TWiLight++, NAND ou Unlaunch.
2. No Windows, extraia DSi_RA_Bridge_Windows_041.zip e execute
   INICIAR_RECEIVER_041.cmd com Node.js. Pare primeiro qualquer receiver
   antigo que use UDP 18216 / HTTP 18217. Abra
   http://127.0.0.1:18217; o painel HTTP só escuta loopback.
3. Baixe receiver.cfg na rota /config escolhendo o IPv4 privado do PC.
   Coloque o arquivo em sd:/DSiRABridge_041/receiver.cfg.
   O formato deve ser exatamente IP_PRIVADO 18216 10.
4. Flipnote Lenny → HBMenu → Fixture_B_041_control.nds. O contador
   deve crescer e A/B mudar a cor. Pressionar Y nesse **controle**
   deve mostrar NO_OBSERVER e não conectar. START sai.
   Se ficar branco, STOP e não executar o launcher.
5. Retorne ao HBMenu e inicie Launcher_A_041.nds. Exigir
   Fixture integrity PASS e modo DSi; se BLOCKED, anotar a mensagem
   sem alterar o exploit. Pressione A para iniciar Fixture B observada.
6. Aguarde o contador B crescer, então pressione Y para conectar.
   Progresso esperado: INIT, ASSOC, WAIT_PEER, READY.
   Caso falhe, fotografe o código NO_CFG / WIFI_FAIL /
   NO_PROFILE / TIMEOUT / LOST. Não modificar roteador.
7. Em READY, acompanhe o receptor 031 original (os rótulos legados
   permanecem por compatibilidade). Pressione A/B durante a sessão.
   Observe sequências UDP, CRC e frames crescentes por ~35 segundos.
   SELECT encerra a sessão. Não deixar engine rcheevos iniciado.
8. Aguarde o observador passar de 1.800 frames, pressione X
   para exportar 53.248 bytes em OBSnnn.bin na pasta 041. Aguarde
   a gravação e deixe contador avançar mais 30 segundos. START sai.
9. Compare o JSON exportado em /export no PC com os valores dos frames
   de OBSnnn.bin usando o decodificador 033 original com proveniência
   HARDWARE_EXPORT. Preserve JSONL como evidência privada, pois pode
   conter endereços IP internos. Não enviar NAND/OTP/tokens/ROMs.

## Interpretação sem voltar a microprobes TWL

- Se o controle e o chainload/OBS PASS, mas Wi-Fi NO_CFG, rever somente
  IP/porta/receiver.cfg.
- Se ASSOC mas não há HELLO, conferir rota LAN/UDP/firewall do aplicativo,
  sem desligar firewall nem mudar a rede inseguramente.
- Se recebe HELLO mas não READY, conferir ACK, nonce, session e modo.
- Se recebe pacotes sem frame crescente, conferir latch latest e
  integridade da janela etiquetada, não memória arbitrária.
- Se recebe UDP e o OBS íntegro com frames correlacionados, comprova
  coexistência do hook externo + Wi-Fi no segundo homebrew específico.
  **Não prova** persistência em retail, monitor residente universal ou
  conquistas oficiais. Sem merge, release ou NAND neste checkpoint.
