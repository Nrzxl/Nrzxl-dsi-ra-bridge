# Limitações e bloqueios
1. Nenhum executor local utilizável; compilar .nds, criar ZIP local e
rodar emulador foi BLOCKED. Fontes estão entregues, não binário.
2. Nrzxl/dsi-ra-bridge retornou 404 pela conexão Nrzxl: inexistente ou
inacessível. A ferramenta disponível não oferece criação de repositórios.
Não foi criado repo nem foram usados HANNA/SATURN como depósito.
3. A receita ARM está escrita para a toolchain clássica. Não afirmar
compatibilidade com libnds 2.x: Calico muda runtime, timers e APIs.
Uma migração moderna é desejável depois de validar a versão inicial.
4. Diagnóstico não testa Wi-Fi, SCFG destravado, WRAM extra, DTCM do
jogo nem permanência depois de lançar outro programa.
5. Não há fork compilado de bootstrap, jogo comercial iniciado,
overlay em tela ou integração com TWiLight validada.
6. O cliente mede sequência, corrupção, duplicação e taxa de chegada.
Latência unidirecional não existe sem relógios correlacionados; aparece
como null. RTT exigirá resposta identificada de um agente, ainda ausente.
7. session não é identidade criptográfica; origem runtime não autentica
hardware; source não libera conquistas. Não usar o protocolo para awards.
8. A captura de 600 registros para automaticamente; não é teste de horas.
Ela não conta VBlanks físicos perdidos independentemente do laço.
9. Fonte do demonstrador rcheevos foi preparada, mas não compilada.
Os testes JavaScript não comprovam o funcionamento de rcheevos.
10. Ler/escrever SD sempre depende de driver/cartão/alimentação. Só são
criadas pastas/arquivos próprios e nenhuma substituição é planejada.
Não é prometido risco zero de falha de filesystem.
11. Não existe método automático de restauração NAND porque não há
alteração NAND. Remoção do projeto no SD é a recuperação prevista.
12. Não foram fornecidos ROMs, BIOS, firmware, NAND, OTP ou console ID.
