# Guia do teste de transporte0.3.2
**Hardware032:NOT_RUN nesta entrega.** Não há conquistas oficiais.
Objetivo físico:600capturados/confirmados/avaliados, sem perda residual,
sem CRC ou avaliação duplicada. Estas são metas, não resultados obtidos.

1. Baixe os artefatos do commit aprovado; extraia no PC os ZIPs internos.
2. Receiver032 em pasta nova. Node.js instalado, sem npm. Pare031 antes
   para liberarUDP18216/HTTP18217. Abra Start-Receiver-032-LAN.cmd.
   Não altera ExecutionPolicy, firewall ou serviços.
3. Abra http://127.0.0.1:18217, escolha o IPv4 privado do Windows e baixe
   receiver.cfg para sd:/DSiRABridge_032/receiver.cfg. Formato:IP PORTA HZ.
   O cfg031 pode ser COPIADO para032 se o IP/porta ainda forem corretos.
4. Copie somente nds/DSiRABridge_032 do ZIP SD para a nova pasta no SD.
   Preserve020/030/031, boot.nds, private/, HBMenu, _nds/, R4 e saves.
   Faça backup de qualquer pasta032 preexistente antes de copiar.
5. Flipnote→Lenny→HBMenu→DSiRABridge_Network_032.nds.
   Y conecta; READY; A inicia600em10Hz (~60s mais eventual backpressure).
6. Ao completar o buffer, o app drena ACKs e tenta FIN/FINACK.
   Aguarde COMPLETE; B também solicita drenagem. Não removerSD durante
   exportação. START aborta e pode deixar dados não confirmados.
7. X exporta sd:/DSiRABridge_032/NETnnn.drb + NETnnn.json com exclusão,
   sem substituir arquivos. Guarde foto de ACKed/pending/retries e estado.
8. No painel exporte DSi_RA_Bridge_032_Result.json e guarde JSONL logs-032.
   Reinicie antes de outra coleta e exporte a anterior antes de usarY.
9. Repita600. Teste interrupção de receiver separadamente, esperando
   falha explícita se houver pendências, sem tratar isso como sucesso.
10. Devolva DRB + JSON do console + JSON/JSONL do receiver e foto/horário.

Painel:Captured/Sent/Received/Recovered/Missing/Duplicated/Evaluated vêm
da seção v2; camposCaptured/Sent dependem do últimoSTATUS recebido.
Confirme com o JSON do console. Malformed/CRC e diagnósticos legados
continuam visíveis, mas não se misturam à contagemv2.
O quadro v2 mostra tentativas originais/retries, ACKs, filas e métricas.
SIMULATED significa teste dePC. RUNTIME_UNVERIFIED não autentica hardware.
Confirmação manual é porSID; não muda elegibilidade oficial.

Auditoria local na raiz do receiver:
    node scripts/audit-capture.cjs C:\dados\NET000.drb
    node scripts/compare-captures-032.cjs C:\dados\NET000.drb C:\dados\NET000.json C:\dados\DSi_RA_Bridge_032_Result.json C:\dados\session.jsonl
O comparador separa integridade dos arquivos de entrega completa e indica
lacunas, fingerprints divergentes e avaliações repetidas.

Simulador dePC opcional (claramenteSIMULATED):
    node windows/receiver-032/simulate.cjs --sender bin/dsirb_sender.exe --frames 600 --faults true --out simulated
Esse piloto usa o helper C de produção e injeta perda66/555 e duplicações.
Não é evidência de rádio ou de execução no DSi.

R semY mantém exportação offline sem inicializarrádio. Offline não avalia
conquistas oficiais e não executa o motor doWindows automaticamente.
Um receiver reiniciado perdeu o estado de avaliação: inicie nova sessãoY;
não se promete retomar uma sessão oficial depois de replay.

Rollback: pare032, abra as pastas031 preservadas e seu NDS031.
Remova somente novas pastas032 depois de salvar evidências.
A PoC residente é um ZIP separado; não é necessária a este ensaio e não
deve ser copiada como atualização do TWiLight/nds-bootstrap.
