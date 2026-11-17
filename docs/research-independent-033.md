# Auditoria de fontes 0.3.3
Fontes primárias inspecionadas em 17/11/2026. Links em commits fixos evitam confundir o estado pesquisado com mudanças futuras.

| Projeto | Referência e evidência |
|---|---|
| DScheevos | [59e9978](https://github.com/skierrz/dscheevos/tree/59e9978be7b9c3788357ef0a609caf9dc8ea74f3); submódulo bootstrap af351f096dd71a37e0e5b18d9709bcc0fb70342f; módulo, ARM7 VBlank, ARM9 idle e pilha própria |
| Bootstrap de DScheevos | [af351f0](https://github.com/skierrz/nds-bootstrap/tree/af351f096dd71a37e0e5b18d9709bcc0fb70342f); patches/cardengines são parte do mecanismo residente, não uma tarefa de HBMenu |
| Loader homebrew | [boot.c](https://github.com/devkitPro/nds-bootloader/blob/a0f819008a63f28c4994e7cc8a8ace892450bbb5/source/boot.c); resetMemory_ARM7, loadBinary, startBinary_ARM7 |
| Loader HBMenu | [nds_loader_arm9.c](https://github.com/devkitPro/nds-hb-menu/blob/3c1f64c12da157fdd14a2d594db139f50e283261/arm9/source/nds_loader_arm9.c); runNdsFile, inode/cluster, sd/fat, VRAM C, chainload flag |
| Calico CRT | [startup.crt0.c](https://github.com/devkitPro/calico/blob/81b75e314d57ed1784545e28554e567f26f572f1/source/nds/startup.crt0.c); loadlists/BSS, MPU, caches, IRQ e heap |
| Calico IRQ | [irq_handler.32.s](https://github.com/devkitPro/calico/blob/81b75e314d57ed1784545e28554e567f26f572f1/source/nds/irq_handler.32.s); seleção e chamada da tabela de handlers |
| melonDS headless | [8a63c88](https://github.com/skierrz/melonDS/tree/8a63c88333c8cb4efed76d866872fc3b6ed0de96/tools/dscheevos); ROM completa, FreeBIOS DS, DLDI FAT sintético, dump e no$gba debug |
| rcheevos | [1433173](https://github.com/RetroAchievements/rcheevos/tree/1433173220a7eaede6a9ed7a18e94117be1821e0); runtime real do projeto, condições locais sem rede |

A arquitetura DScheevos reserva aproximadamente 2 MiB em 0x02D80000–0x02F80000 e reduz o cache de ROM. Capturas e avaliação têm caminho de idle para evitar trabalho pesado no IRQ/stack do jogo. A presença de código para DSi não é evidência de validação no DSi XL via Flipnote Lenny; o estado upstream experimental e dependências devem ser respeitados. Esta PoC não copia o módulo GPL para código MIT.

Bloqueios: a montagem interna do SD e a cadeia de permissões Lenny→HBMenu→A→B ainda não foram verificadas nesta entrega. O protocolo Wi-Fi032 continua com PEER TIMEOUT físico. Um servidor iniciado no PC e uma tabela vazia não identificam sozinhos a causa do timeout.

Detalhe decisivo: [start.s](https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/dscheevos/module/src/start.s) define vblank_entry como stub; halt_entry verifica IRQ/IME, MPU, caller idle e guard antes da troca de pilha. [module.c](https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/dscheevos/module/src/module.c) contém vblank_poll/cópia/avaliação. [dscheevos_hooks.c](https://github.com/skierrz/nds-bootstrap/blob/af351f096dd71a37e0e5b18d9709bcc0fb70342f/retail/bootloaderi/source/arm7/dscheevos_hooks.c) carrega módulo/sessão, patchOsHalt procura a assinatura ARM mov/mcr/bx, habilita os cardengines e solicita ARM9_DSCHEEVOS_INIT. O comentário inicial desse arquivo sobre IPC/VBlank está desatualizado frente à implementação atual; o corpo do código e start.s prevalecem.

Fontes de compatibilidade: [hardware-access](https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/docs/hardware-access.md) distingue o caminho retail híbrido do loader homebrew, sem cardengine residente. [original-ds-and-flashcarts](https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/docs/original-ds-and-flashcarts.md) discute limites de RAM/CPU/driver no R4; estimativas de DSpico não são evidência medida. [DSi Guide](https://dsi.cfw.guide/launching-the-flipnote-exploit.html) documenta a entrada sem Unlaunch. Nenhuma instrução de troca de boot.nds/NAND desse guia é executada aqui.
