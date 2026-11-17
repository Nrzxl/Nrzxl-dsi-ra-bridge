# Teste removível 0.3.3 — hardware NOT_RUN
Este pacote só é liberado pelo CI após emulação completa DS/NTR. Isso não valida o DSi XL nem Flipnote Lenny.
Não copie o executável EMU_ONLY no SD físico. Não substitua boot.nds, private, HBMenu, TWiLight, nds-bootstrap, R4 ou arquivos anteriores.

1. Desligue o console. Extraia o ZIP SD em uma pasta no PC. Confirme que só contém as pastas novas nds/DSiRABridge_033 e DSiRABridge_033. Se já existirem, preserve uma cópia e use outro cartão/pasta de teste; não sobrescreva.
2. Copie essas duas pastas novas para o SD interno. Não mexa no microSD do R4. Não há ROM comercial neste pacote.
3. Inicie Flipnote Lenny e o HBMenu pelo procedimento já funcional.
4. Primeiro abra nds/DSiRABridge_033/Fixture_B_033_control.nds. Aguarde 35 segundos, pressione A e B, observe o contador avançar e as cores mudarem. X deve informar ausência da janela marcada. START retorna pelo mecanismo normal do HBMenu; se não retornar, desligue normalmente após cessar atividade do SD. Registre o resultado como controle.
5. Reinicie o mesmo caminho até HBMenu. Abra nds/DSiRABridge_033/Launcher_A_033.nds. Deve mostrar integridade PASS e modo DSi. Se indicar BLOCKED, fotografe a mensagem e encerre; não altere permissões ou instalação.
6. Pressione A uma vez. Deve aparecer Independent Fixture B033 e o contador continuar. O launcher foi encerrado; B executa sua inicialização ARM9 e ARM7 próprias. O observador é um hook externo inserido na cópia experimental de B.
7. Aguarde pelo menos 35 segundos, pressione A e B durante esse período e depois X. A gravação só ocorre no SD interno, em DSiRABridge_033/OBS000.bin ou próximo número livre, sem sobrescrever. O arquivo esperado tem 53.248 bytes. Durante a escrita aguarde a mensagem de conclusão.
8. Observe mais 30 segundos para confirmar que o contador continua; pressione START. Desligue antes de retirar o SD.
9. Devolva somente OBSnnn.bin e fotos das telas de A e B, com o tempo aproximado e eventuais travamentos. Não envie NAND, OTP, console ID, ROM ou saves.

O export só inclui uma janela fixa marcada do laboratório, sem pilha privada. Os 1.200 registros ficam estáveis; os contadores de resumo continuam mudando, portanto o arquivo inteiro não é um snapshot atômico.

Windows: instale Python 3.10+ da fonte oficial, extraia o pacote Windows e execute:
`python decode.py OBS000.bin --provenance HARDWARE_EXPORT --engine engine/dsirb_live.exe --output resultado-033.json`
A execução local de rcheevos usa condições artificiais identificadas LOCAL_TEST_ONLY, sem autenticação, HTTP ou concessão oficial.

Critério físico: contador B >=1800, observador >=1800 chamadas, 1200 registros ordenados íntegros e observação continuada depois de encher o buffer. Exportações vazias, tela congelada ou BLOCKED não são PASS. Para remover, apague somente as duas pastas novas após copiar os resultados para o PC. Nada foi instalado na NAND.

Diagnóstico paralelo do PEER TIMEOUT032: encerre o receiver032 para liberar UDP18216. No PC execute python hello_only_032.py --seconds 30. No DSi abra somente o aplicativo032 já existente e pressione Y, sem A. O log novo registra HELLO recebido, ACK enviado e falhas. Um ACK enviado não prova recepção no DSi; só READY/contadores do console completam a evidência. O utilitário nunca ACKa DATA. Sem pacotes, verificar arquivo receiver.cfg, IP LAN, rota e firewall; com ida sem volta, investigar retorno/validação C. Não desative firewall ou mude rede automaticamente.
Auditoria de formato, sem alterar configuração: python hello_only_032.py --config CAMINHO/receiver.cfg. Compare o IP mostrado com o PC atual; formato válido não comprova conectividade. Os logs podem conter IP privado: devolva-os em privado, não publique no repositório.
Hash legítimo futuro: engine/dsirb_nds_hash.exe COPIA_ORIGINAL.nds calcula somente o hash oficial Nintendo DS com rcheevos. É somente leitura e não identifica um jogo no servidor nem inicia sessão. Não use a imagem instrumentada para identificar o original.
