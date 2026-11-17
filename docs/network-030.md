# DSi RA Bridge 0.3.0 — rede experimental
Este é um aplicativo independente. Não monitora outro jogo e não envia
conquistas ao RetroAchievements. Preserve o diagnóstico 020 já testado.

## Receiver Windows
Baixe o artefato Receiver 030 da execução GitHub Actions e extraia em uma
pasta NOVA. Ele contém o motor rcheevos compilado para Windows, scripts,
interface HTML e licença. É necessário Node instalado; não instala serviços.

Abra PowerShell na pasta e execute, para a rede local:
.\windows\receiver\Start-Receiver.ps1 -Lan
Abra http://127.0.0.1:18217. A interface web fica somente em loopback.
UDP recebe na porta 18216. Sem -Lan, o receiver aceita apenas localhost.
A página mostra IPs privados do Windows. Escolha o IP do adaptador que está
na mesma rede do DSi; conexões VPN podem listar endereços que não servem.
Pode baixar receiver.cfg pela página, ou criar manualmente um arquivo:
192.168.0.2 18216 10
São IP do PC, porta e frequência; substitua pelo IP correto do seu PC.

Copie receiver.cfg SOMENTE para sd:/DSiRABridge_030/receiver.cfg, uma pasta
nova. O arquivo não contém SSID, senha, token ou configuração permanente.
No aplicativo, D-pad altera IP/porta/Hz enquanto o worker está parado.
Campos 1–4 são octetos, 5 é porta, 6 frequência. Apenas endereços privados.

## Firewall e rede
O programa não altera firewall, roteador ou perfis do Windows.
Se o receiver estiver ativo e o DSi parar em WAIT RECEIVER, verifique
IP, sub-rede, rede de convidados e isolamento entre clientes do access point.
Para uma rede de confiança com perfil Private, uma regra opcional restrita
pode ser criada pelo usuário em PowerShell elevado:
New-NetFirewallRule -DisplayName "DSi RA Bridge UDP 030" -Direction Inbound -Action Allow -Profile Private -Protocol UDP -LocalPort 18216 -RemoteAddress LocalSubnet -Program (Get-Command node).Source

Não execute a regra em rede pública ou no roteador. Não encaminhe porta na
internet e não reduza a segurança do seu Wi-Fi principal para WEP.
Uma rede 5 GHz ou WPA3-only não é alvo presumido deste experimento; use
a rede 2,4 GHz compatível já configurada no DSi, sem alterar chaves aqui.
A disponibilidade de WPA2 pelo Flipnote Lenny ainda precisa de teste físico.

## DSi
Adicione somente a pasta nova do ZIP SD validado ao SD interno, com o
console desligado e backup prévio. Cancele qualquer substituição.
Abra Flipnote Studio → Flipnote Lenny → HBMenu → nds/DSiRABridge_030.
Y inicia conexão; A alterna transmissão; B solicita parada; START encerra.
X exporta .drb só depois de o worker encerrar, evitando I/O de SD e rede
concorrentes durante a exportação.

| Tela | Interpretação possível |
|---|---|
| INIT | Inicialização SDK/ARM7; UI continua ativa |
| INIT FAILED | SDK não inicializou; não prova causa específica de hardware |
| NO SAVED PROFILES | Nenhum perfil utilizável carregado pela API |
| ASSOC/DHCP | Associação e obtenção de IP, até 30 segundos |
| LINK TIMEOUT / LINK LOST | Perfil, sinal, DHCP ou permissões precisam de diagnóstico |
| WAIT RECEIVER | Rádio/IP alcançados; handshake UDP ainda ausente |
| PEER TIMEOUT | Dez segundos sem handshake válido |
| READY | Receiver respondeu à sessão; A libera coleta |
| STOPPED | Worker encerrou; X permite exportação |

Inicialização tem watchdog de 20 segundos na UI. Ele solicita cancelamento;
não promete interromper uma chamada interna travada do SDK. START não faz
join indefinido: após dois segundos encerra o aplicativo pelo mecanismo do
loader. Retorno exato ao HBMenu depende do bootstub. Um timeout deve ser
documentado com foto, sem instalar Unlaunch para contornar.

O buffer comporta 600 amostras, padrão 10 Hz (~60 segundos nominais).
Taxas disponíveis: 1–30 Hz. Existe apenas um slot de transmissão; overflow
é contado. Esses snapshots não são capturas por cada frame do jogo.
Os valores são quatro palavras controladas do próprio aplicativo.
readTicks agora usa ticks monotônicos Calico; não compare diretamente com
os ticks de timers do diagnóstico 020.

## Origem e medições
SIMULATED: produzido pelo simulador do computador.
RUNTIME_UNVERIFIED: origem declarada por DS/DSi, sem autenticação física.
PHYSICAL_CONFIRMED_MANUALLY: declaração explícita do usuário com nota de
evidência, limitada àquela sessão. Nunca é ativada por pacotes de rede.
O modo DSi também pode ser produzido por um emulador.
CRC protege contra corrupção acidental; não autentica hardware.

O receiver mede RTT enviando nonce e recebendo eco do portátil. RTT inclui
processamento e espera no DSi. Não o divide por dois como se fosse latência
unidirecional. Lacunas são inferidas por sequência e diminuem quando um
pacote atrasado da janela retida é recuperado. Histórico é limitado a
1024 posições por sessão e no máximo oito sessões; logs têm backpressure.
Pacotes tardios não são reenviados para o motor fora da ordem.

## rcheevos experimental
O executável dsirb_live usa rc_runtime oficial no commit
1433173220a7eaede6a9ed7a18e94117be1821e0. Não inclui rc_client, HTTP ou login.
As condições locais usam IDs de teste 1/2: contador >=120 e >=300.
Uma condição medida mostra progresso. O motor recebe só a primeira sessão
selecionada automaticamente; seu ID aparece na interface. Reinicie o
receiver para escolher outra sessão antes do teste físico.
Ele arma definições com um frame falso explicitamente sintético.
Isso é demonstrador, nunca evidência para desbloqueios oficiais.
O receiver informa “NÃO ENVIADAS AO RETROACHIEVEMENTS”.

## Devolver evidências
Após testar, devolva NETnnn.drb, uma foto da tela, JSON exportado do receiver
e manifest.json do build usado. Logs podem conter IP privado e sua nota;
revise antes de compartilhar. Não envie NAND, OTP, configurações Wi-Fi,
tokens, dumps de RAM geral ou jogos.

## Pesquisa utilizada
Foram inspecionados os fontes oficiais dswifi/calico:
https://github.com/devkitPro/dswifi/blob/a80539fa8ede95f65bba416b7ffcba2c05dbdecf/source/dswifi9.c
https://github.com/devkitPro/dswifi/blob/a80539fa8ede95f65bba416b7ffcba2c05dbdecf/source/wfc.c
https://github.com/devkitPro/calico/blob/81b75e314d57ed1784545e28554e567f26f572f1/include/calico/dev/wlan.h
https://github.com/devkitPro/calico/blob/81b75e314d57ed1784545e28554e567f26f572f1/include/calico/system/thread.h
O wrapper oficial WFC_CONNECT espera associação em um laço; esta aplicação
usa INIT_ONLY em worker, conexão assíncrona e timeouts externos.
A API WFC contempla perfis DSi estendidos e autenticação WPA. Isso não
prova permissões ou compatibilidade no DSi físico via Flipnote Lenny.
Não foi portado um driver SDIO próprio ou o protocolo do xeRAbora.
