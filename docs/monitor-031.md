# Próximo marco: agente entre dois programas homebrew
Pesquisa consultada em17/11/2026. **Plano**, não monitor persistente implementado.
A031 lê apenas os quatro valores controlados do próprio homebrew.
Não há prova de que o seu worker, Calico ARM7 ou associação Wi-Fi sobrevivam
a carregar outroNDS. Um segundo programa pode reconfigurarCPU,IRQ,MPU,
FIFO,MBK,SCFG,SDIO e limpar aRAM. Uma thread não é um processo residente DS.

## Fontes verificadas e implicações
- nds-bootstrap upstream f6728baaa28a6fffbd070badce60d0b470180e1e:
  retail/bootloader/source/arm7/hook_arm9.c contém hookNdsRetailArm9 e
  encontra tabela deIRQ por assinaturas. Há CE9/CE7 separados, inclusive
  retail/cardenginei. Nem toda chamada CE9 é uma fronteira de frame.
  hb/bootloader/source/arm7/hook.c tem detecção específica do dispatcher
  homebrew. Não se pode importar o hookNitroSDK paraCalico por suposição.
- dscheevos 59e9978be7b9c3788357ef0a609caf9dc8ea74f3:
  docs/architecture.md,docs/hardware-access.md,module/src/module.c,
  module/module.ld ecore/src/dscheevos.c foram inspecionados.
  OREADME declara WIP,não aprovadoRA e sem ensaio físicoDSi.
  Seu texto atual já evoluiu além de copiar memória noVBlank:
  CE7 conta frames, ARM9 usaOS_Halt no idle, captura no último halt válido,
  avalia fila e rede fora deIRQ, com stack própria.
  Há caminhosfallback que usam leituras live ou repetem último snapshot:
  exigem auditoria semântica antes de reutilizar para awards.
- Código dscheevos reserva2MiB0x02D80000–0x02F80000 do cacheROM,
  nãoRAM universalmente livre. module.ld separa código/data aliases eMPU.
  Essa reserva é específica dofork/loader e não cabe copiar no SD.
- Oshim ARM7Wi-Fi doDScheevos é específicoSDIO; não é o ARM7Calico default.
  A arquitetura relata evitarpollSDIO duranteSD read e pausa ao jogo usar
  rádioDS. Tais medidas são evidências de conflito potencial, não prova
  de que nossa031 pode coexistir com jogos.
- O próprioDScheevos registra que homebrew usa caminhoHB e BIOSwait,
  nãoOS_Halt doNitroSDK. É necessárioABI explícito para os dois programas
  próprios antes de procurar assinaturas em código de terceiros.

Links de origem:
https://github.com/DS-Homebrew/nds-bootstrap/tree/f6728baaa28a6fffbd070badce60d0b470180e1e
https://github.com/skierrz/dscheevos/tree/59e9978be7b9c3788357ef0a609caf9dc8ea74f3
https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/docs/architecture.md
https://github.com/skierrz/dscheevos/blob/59e9978be7b9c3788357ef0a609caf9dc8ea74f3/dscheevos/core/src/dscheevos.c

## Arquiteturas
|Opção|Vantagem|Bloqueio|Decisão|
|---|---|---|---|
|Dois programas cooperativos próprios+ABI reservado|Sem buscar assinatura comercial;mapas verificáveis|Loader/startup devem preservarIRQ,RAM,ARM7|PróximaPoC isolada,primeiro offline|
|ForkDScheevos/nds-bootstrap retail|Há infraestrutura dehooks,cache eidle|GPL,ABI complexo,Wi-Fi diferente,sem prova física dofork|Referência;não distribuir umbuild como validado|
|Substituir ARM7 do jogo peloCalico031|Reuso aparente do transporte|Quebra áudio,FIFO,SD e rotinas do jogo|Não implementar assim|
|Só app separado antes/depois do jogo|Seguro e removível|Não lêRAM durantejogo|Diagnóstico atual;insuficiente paraRA|

Rota proposta para aPoC: launcherExperimental.nds e payloadHomebrew.nds
combinados com imagemresidente própria e manifestos de segmentos. Nenhum
arquivoem_nds nem instalação estável é substituído. O linker deAMBOS deve
excluir regiãoresidente,stack,ring,headerABI e guards; validar todos os
intervalos deELF antes deboot. Fase inicial nem inicializaWi-Fi. A inicialização
depayload é parte do experimento e não pode usar um loader genérico que
apagueRAM/IRQ/ARM7. OABI terá attach/detach,frame counter,cancel,reset epoch,
tabela allowlist e callbacksbounded. Esse protocolo ainda não foi implementado.
Não criar um segundoNDS que apenas reinicie oconsole e chamá-lo persistência.

Gate1: residente coleta porframe umcontador,pointer ealvo que o segundo
programa atualiza,com chaves/guardsantes/depois;6000framesem ordem;
inclui cache sujo,DTCMrelocável,reset,IRQ substituída,falta deidle eoverflow.
Provar peloPC eELFmap que instruções doagente/stack ficamforado payload.
Gate2: áudio einput ativos,A/BtimeVBlanksem monitor ecommonitor.
Gate3: anexar transporte eARM7 integrado,demonstrar coexistência comSD.
Sódepois estudarretail porforkseparado e jogos próprios dumps.

## Frames, memória e orçamento
AvaliaçãoRA precisa acompanhar cadaframe lógico;10Hz serve diagnóstico,
não condições deumframe,hits,delta/prior ouponteiros transitórios.
Captura e envio devem ter frequências independentes. Por exemplo,60
snapshots/s de64B são3840B/s de payload,maisUDP/IP28B por datagrama
=5520B/s semWi-Fi,ACKs,controle ouretries. Batching6frames em10datagramas/s
exige umNOVO envelope versionado,mas mantém6frames individuais,ordenados.
Não descartar5de6frames paraeconomizarrede.

16B allowlist x60Hz exige apenas960B/s deRAM copiada. Já4096B x60
=245760B/s e,comoverheadpor datagrama,fragmentação/latênciaprecisam
medição. Umring128x64B custa8192B e cobre~2.13s; orçamento hipotético,
não reserva validada. Oprobe atual tem600x64=38400B,workerstack32768,
mais600BtxOutcome eSDK;ELF/map/size dos artefatos quantificam obuild.
Metainicial paraPoC, não medição: custoARM9<0.5ms/frame,mediana/p95/pior,
frames missed=0; ultrapassar orçamento bloqueia suporte àquele cenário.

Leitura deDTCM deve serARM9, base lida deCP15 do contextoexecutado, sem
supor basefixa. EndereçoRA é lógico e diferente dofísico. CacheARM9 impede
usarARM7 comoespelho coerente; limparcache global a60Hz pode prejudicar
o jogo. Capturarallowlist e todosalvos deponteiros nomesmoepoch; mudanças
durante captura invalidamoframe, não preencherfaltantescomzero. ParaDMA,
interrupçõesmascaradasnãoimpedemtodososprodutores; protocolo depublicação
cooperativo epseudoseqlocké parte dofixturepróprio, não garantiaretail.

Overlays,heap,stack,ROMcache eDTCMprecisam intervalosdeexclusão. Sem
reserva docarregadorprovada porlinker/map, nãoescrever nem carregaragente.
Reset exige novoepoch,drain/cancel,limpeza deestadoRA eproibiçãodereplay.
Wi-Fi/áudio:umdonoparaFIFO/IRQ/ARM7,semusar driverconcurrente; jogo
multiplayerpodebloquear redebridge atédesligarorádio do jogo.
OS_Halt nãoexisteou faltatempoidleemalgunsjogos:marcarunsupported, não
inserir avaliação pesada noVBlank comoalternativa automática.

## Caminho oficialRetroAchievements
rcheevos local continua upstream1433173220a7eaede6a9ed7a18e94117be1821e0
(MIT),semrc_client/HTTP/token/award nesta031. Condições1/2 nãosãoIDsRA.
Próximagateserviços:rc_hashDS daROMrealmenteexecutada (nãoMD5doarquivo
inteiro),mapadeRAM/DTCM validado,framesíntegros,rc_clientcomHTTPHTTPS,
User-Agentpróprio,autenticaçãoeproteçãodetokennoWindows,políticaoficial
decliente/hardcoreverificada comRA antes dehabilitarenvios. Nenhuma
simulação,replay outestecontrolado devealcançarocaminhodeaward.
Nãosolicitarcredenciaisnestaetapa.

Licenças:nds-bootstrap eDScheevosGPL-3.0. Nãofoicopiado seucódigo para
oCoreMIT031. Umaalteração/forkdistribuído requerGPL,fontes correspondentes,
avisoselicençasdependências. Conceitosdocumentados nãosãobuildemprestado.
