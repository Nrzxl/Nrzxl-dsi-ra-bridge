# 0.3.4-Q — auditoria somente offline

DSi XL Flipnote Lenny → HBMenu: P0 CONTROL recebeu STAGE 1 e 2 REACHED; P1 UPDATE_LINK travou em telas brancas; P2 FIFO_LINK segue BLOQUEADO.

O 034Q recompila O2/P0/P1 usando BlocksDS 1.24.0 pinado e gera relatório de ELF/NDS com seções, endereços VMA/LMA, .twl/.twl_bss, símbolos e membros de bibliotecas .a selecionados pelo linker. A auditoria é estática; não conecta ao console, não altera SD, não usa rede e não publica arquivo .nds para instalação.

Não atribuir causa a Wifi_Update em execução, pois a função não foi chamada. A presença de símbolos ou segmentos novos no ELF é somente pista. Memória MBK/NWRAM real do DSi não foi medida.

Baixar AUDITORIA_034Q.md/JSON e mapas do workflow para analisar antes do 034R. Não repetir P1 nem executar P2. Não mexer em boot.nds, _nds, private, NAND ou Unlaunch.