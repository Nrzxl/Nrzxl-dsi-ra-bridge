# DSi RA Bridge 0.3.1 — teste independente
Versão experimental; DSi físico **NOT_RUN** para esta versão até nova evidência.
A comunicação física 030 foi relatada pelo usuário e seu JSON foi inspecionado;
não confundir esse marco com homologação 031. Nenhum envio oficial RA é implementado.

## Arquivos e preservação
Baixe os dois artefatos do Actions **do mesmo commit** na branch
fix/dsi-ra-bridge-network-stability-031. Cada download do GitHub contém um ZIP
interno: SD_031_UNVALIDATED e Receiver_031.
Não extraia o artefato inteiro com executáveis ELF/logs no SD.
Extraia o ZIP interno SD primeiro numa pasta temporária e confira SHA256SUMS.txt.
O binário fica em nds/DSiRABridge_031/DSiRABridge_Network_031.nds.
Copie apenas essa nova pasta para sd:/nds/DSiRABridge_031 e o guia opcional.
020/030, boot.nds, private/, HBMenu e _nds/ não são substituídos.
Se algum caminho 031 já existir, preserve-o com outro nome antes de copiar.
O pacote não contém configurações ou saves pessoais.
Faça uma cópia de segurança do SD antes de testar.

## Windows 10/11
Requisito: Node.js instalado (a versão usada no CI está nos logs). Sem npm.
Extraia Receiver_031 numa pasta nova, separada da 030.
Dê duplo clique em **Start-Receiver-LAN.cmd** na raiz do pacote.
Ele chama Node diretamente; não altera ExecutionPolicy, Registro, firewall
ou serviços. O motor nativo bin/dsirb_live.exe acompanha o pacote Windows.
Alternativa: windows/receiver/Start-Receiver.cmd (somente loopback) ou
Start-Receiver.cmd --lan. O .ps1 continua disponível, sem mudança de política.
O painel HTTP fica exclusivamente em http://127.0.0.1:18217.
UDP é 18216. Pare o receiver030 antes de iniciar031, para evitar porta ocupada.
Uma regra existente de firewall para Node pode precisar ser autorizada pelo
Windows para a rede privada; o iniciador não cria regras nem pede administrador.
Não desative firewall ou segurança do roteador.

No painel escolha o IPv4 correto do Windows na lista (evite VPN/adaptador virtual).
Baixe receiver.cfg e coloque-o em **sd:/DSiRABridge_031/receiver.cfg**.
É uma linha: IP_PRIVADO 18216 10. Pode copiar o cfg030 para a nova pasta031
se o IP do PC ainda for o mesmo. Nenhuma credencial Wi-Fi é incluída.
O aplicativo usa perfis já salvos no console, somente leitura, como030.

## Console — repetição controlada
1. Flipnote → Lenny → HBMenu → sd:/nds/DSiRABridge_031/DSiRABridge_Network_031.nds.
2. Confira modo, IP, porta e 10 Hz. Y conecta; aguarde READY. A inicia coleta.
3. Aguarde Stored 600/600 (~60 s a 10 Hz). Não inicie jogos.
4. Fotografe tela do console e painel. Registre Tx calls, sent, failed e queue drops.
5. B para; espere worker parado. X exporta DRB e JSON do transmissor.
6. Encontre sd:/DSiRABridge_031/NETnnn.drb e NETnnn.json. Os nomes são
   criados com exclusão (O_EXCL); não substituem capturas anteriores.
   "JSON FAILED" significa que DRB pode existir sem metadados completos.
7. No painel baixe DSi_RA_Bridge_031_Result.json e guarde o JSONL indicado
   em logs-031. Copie os arquivos depois de parar/fechar o receiver.
8. Feche e abra o app; repita uma segunda sessão para verificar estabilidade.
   Y cria nova sessão e limpa o buffer em RAM: exporte a anterior antes.
9. Teste desconexão encerrando o receiver após algumas amostras. Verifique
   WAIT RECEIVER/PEER TIMEOUT. Reinicie receiver e tente Y novamente.
   Não use esse ensaio como sessão contínua oficial.
10. Offline: abra novamente e aperte R antes de Y. A pausa/retoma, B pausa,
    X exporta. Nenhum rádio é inicializado nessa rota.

START solicita saída; init do SDK ainda pode exigir reiniciar o aplicativo
caso não termine, como na030. Não foi alterado o mecanismo de inicialização,
associação, DHCP, nem o ARM7/driver oficial. Novo teste físico é obrigatório.

## Como devolver evidências
Envie o par NETnnn.drb + NETnnn.json, o resultado do receiver e o JSONL
da mesma sessão, mais foto/horário aproximado. Esses arquivos contêm IPs
privados, endereços da região controlada e diagnóstico: envie aqui, não
publique no repositório. Não envie NAND, OTP, credenciais ou firmware.
Se o receiver mostra SIMULATED, o ensaio não é de hardware.
RUNTIME_UNVERIFIED é um pacote de agente; não prova console físico sozinho.
Confirmação manual no painel apenas registra sua declaração por sessão.

Validação binária no Windows, na raiz do receiver:
    node scripts/audit-capture.cjs C:\caminho\NET000.drb
O validador não transforma replay em evidência de execução física.

## Interpretação do painel
- Snapshots: apenas avanço de sequência alimenta o motor; duplicatas, conflito
  de conteúdo e fora de ordem não avaliam conquistas de novo.
- Duplicatas exatas: mesmo número e SHA256 dos 64 bytes na janela de1025.
  Número igual com conteúdo diferente é CONFLICTING_SNAPSHOT.
- HELLO repetido é heartbeat intencional. PONG conhecido já respondido
  é contado separadamente. Nenhum deles incrementa duplicatas de snapshots.
- Malformed: wire com comprimento/header/tipo/valor inválido.
  CRC tem contador próprio; causas ficam em totals.reasons.
- Controle válido em estado errado não é erro de wire: aparece em
  UNEXPECTED_CONTROL_STATE. Tardio identificado aparece em LATE_PACKET.
- Contadores totais nunca são escondidos. Há até64 diagnósticos recentes;
  o JSONL limita detalhes de anomalias a60/s; diagnosticsSuppressed e
  logDropped tornam a supressão/backpressure visível.
- Hz configurado031 vem do nonce HELLO documentado. Agente030 mostra
  desconhecido; não inferimos configuração do valor medido.
- Hz medido é média dos snapshots aceitos entre primeiro/último. Pacotes/s
  inclui controles/repetições; pausa afeta médias.
- RTT tem atual/mínimo/média/máximo, medido por desafio do Windows.
  Não é latência de ida. ACTIVE significa agente responsivo, não streaming.
- O motor acompanha só a primeira sessão selecionada. Reinicie o receiver
  para mudar; sessões não se misturam. IDs1/2 são condições locais de teste.
  submitted:false e officialEligible:false permanecem obrigatórios.

## Rollback
Pare o receiver031 e inicie sua pasta030 preservada. No HBMenu abra030.
Para remover031, apague somente as novas pastas031 depois de copiar os logs.
Nunca substitua boot.nds, exploit, kernelR4, _nds/ ou saves.
