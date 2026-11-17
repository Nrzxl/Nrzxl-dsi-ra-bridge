# Escolha de arquitetura e caminho a RetroAchievements —032
Pesquisa em17/11/2026. Código inspeccionado por commit, não apenasREADME.
Não foi instalado nenhum fork debootstrap no SD.

## Baselines reproduzíveis
| Projeto | Revisão consultada | Evidências |
|---|---|---|
| DSi RA Bridge031 |597fd0edac3a1b5c5ecb8a38aeca14adb7aeb443|fonte,JSONsender/receiver eJSONL físico fornecidos|
| DScheevos |59e9978be7b9c3788357ef0a609caf9dc8ea74f3|README,docs/architecture.md,hardware-access.md,moduleABI/linker/module.c,core|
| nds-bootstrap upstream |f6728baaa28a6fffbd070badce60d0b470180e1e|retail hook_arm9.c,HB hook.c ecardengines|
| ForkBakkerrrs |4d60695487a5593531c0c395e8d4d1ae2ca91fad|ra.h,ra_reader.c,ra_rcheevos.c,ra_net.c,docs/retroachievements.md|
| rcheevos executado nos testes |1433173220a7eaede6a9ed7a18e94117be1821e0|rc_runtime real eLICENSE MIT|
| rcheevos API atual |include/rc_client.h ehash.c no master consultado|contratoslogin/load/memória/servercall; não incorporado ao build|
| SimuladorCPU |Unicorn2.1.4 release oficial|binárioSHA256verificado; modeloARM946; sememulaçãoDS|

Links:
https://github.com/skierrz/dscheevos/tree/59e9978be7b9c3788357ef0a609caf9dc8ea74f3
https://github.com/DS-Homebrew/nds-bootstrap/tree/f6728baaa28a6fffbd070badce60d0b470180e1e
https://github.com/Bakkerrrs/Retroachievements-DS-on-3DS/tree/4d60695487a5593531c0c395e8d4d1ae2ca91fad
https://github.com/RetroAchievements/rcheevos/blob/1433173220a7eaede6a9ed7a18e94117be1821e0/LICENSE
https://github.com/RetroAchievements/rcheevos/blob/master/include/rc_client.h

## Descobertas relevantes
DScheevos já tem a arquitetura mais completa voltada ao DSi: launcher,
hash/sessão, módulo reservado, integração decardengine, avaliaçãoemidle,
HTTPS, filas e reset. SeuREADME declara WIP, não aprovadoRA e nenhum
teste físicoDSi próprio. ResultadosmelonDS reportados são do projeto,
não validação nossa. Ele carrega um fork dercheevos com dez patches;
não trocar nossa referência upstream por essefork sem teste diferencial.

Na arquitetura atual, CE7 contaVBlanks; ARM9 captura no últimoOS_Halt
apropriado, avalia noidle e trabalha com dados próprios/stack separada.
Há proteçãoMPU e caminhosfallback para leituraslive/repetição de snapshot.
Isso exige auditoria de semântica em lagframes e ponteiros, não apenas
confirmar que algum trigger ocorreu.
A reserva de2MiB em0x02D80000–0x02F80000 reduz o cacheROM nofork; não é
RAM livre geral doDSi. TWL games podem ocuparRAMque NTR não usa.
A rede dentrodojogo usa shimSDIO/ARM7, lwIP eTLS, evitando conflito com
leiturasSD e rádioDS. Não se preserva isso copiando o workerCalico032.
Jogos que não oferecemOS_Halt/idle suficiente permanecem um risco real.

No forkBakkerrrs, a exclusãoDSi está comprovada no código:
retail/cardenginei/arm9/source/ra_reader.c, funçãora_tick:
consoleModel==0 retorna sem monitorar. O escopo é3DS, não uma demonstração
de impossibilidade física doDSi. As variantesDLDI/GSDD também são
desativadas por padrão emra.h por espaço/caminho deinstalação.

Há documentação desatualizada nesse fork. OREADME diz client/net não
iniciados, mas a revisão atual contém ra_rcheevos.c com rc_runtime,
staging/unlocks e ra_net.c com login/gameid/startsession/unlocks.
Portanto a conclusão correta não é “não há motor/rede no código”.
rc_client é deliberadamente ausente; a sessão é gerida pelo launcher.
O runtime inclui frameSkip adaptativo. Observar alguns unlocks com
frames pulados não prova fidelidade de hits/delta/prior ou condições
transitórias. Não reutilizar isso como autorização para nossa captura10Hz.

Outro ponto decisivo: ra_net.c declara transporteHTTP em porta80 e
credenciais em claro. Essa rota não será utilizada peloBridge.
O Windows pode oferecerHTTPS/TLS sem esse compromisso no portátil.
Um texto dessefork chama rcheevos deGPL; oLICENSE do upstream realmente
usado éMIT. O licenciamento deve seguir o código/licença correspondente.

O upstreamnds-bootstrap tem cardengines/injeção e detecção deIRQ por
assinaturas; não é um sistema operacionalcom processos residentes.
CaminhosHB/retail e ARM7 diferem. Um jogo/loader pode apagarRAM, mudar
MPU/cache/WRAM,IRQ,FIFO e drivers, encerrando nosso agente atual.
A PoC cooperativa032 evita esse problema por contrato explícito; não
demonstra que o problema geral foi resolvido.

## Comparação das quatro rotas
| Rota | ViabilidadeDSi | Esforço / risco | Windows | Caminho oficial |
|---|---|---|---|---|
| Monitor inteiramente novo noBridge | Não demonstrada além dofixture próprio | Muitoalto:recriarloader,hooks,mapas,ARM7 eframes | Opcional | Máxima responsabilidade de correção; nenhum suporte atual |
| Adaptar componentesDScheevos | Mais evidência arquitetural; físico pendente | Alto, porém evita reinventarcardengine/reservas | Pode ser usado como engine/TLS | Requerframes/mapas/hash/autenticação e avaliação de confiança |
| DScheevos como baseexperimental separada | Melhor protótipo integrado descrito paraDSi | Menor esforço paraavaliarloader; aindahardware desconhecido | Não necessário na arquitetura original | Não é aprovação doRA nem compatibilidade física provada |
| Bridge como receiver/telemetria complementar | Transporte próprio já tem evidência física031 | Menor risco; não resolve captura nojogo sozinho | Sim | Bom oráculo paracomparação eHTTP/TLS protegido; ainda não cliente oficial |

## Decisão
Não reconstruir todo nds-bootstrap dentro doBridge.
Para o monitorretail, o próximo baseline deve ser **DScheevos em um forkGPL
separado**, primeiro no modo sem submissões/credenciais, comparando sua
captura com um fixturepróprio e o engine upstream doWindows.
OBridge032 permanece transporte, auditoria e oráculo complementar.
Após provar captura noDSi, testar a variante híbrida: módulo GPL de
memória noDSi + avaliação upstream/TLS/autenticação noWindows.

É uma escolha por evidência existente e menor trabalho duplicado, não uma
promessa de que oDScheevos já funciona com FlipnoteLenny. O fork3DS é uma
referência útil de reader/overlay, mas remover consoleModel==0 não basta:
IRQstack,WRAM,MPU,tempoCPU e transporte precisam deport/ensaios próprios.
SeuHTTP em claro e frameSkip não são uma base direta para awards.

## Gate específico do ambiente Lenny
O teste031 prova acesso aSD, RAM própria eWi-Fi emmodoDSi. Não prova
as permissõesSCFG/MBK/WRAM esperadas pelo bootloaderDScheevos, nem que
a associação sobrevive ao carregamento do jogo.
Os documentos dehardwareDScheevos descrevem estados típicos de frontends
com Unlaunch/hiya; não assumir equivalência comLenny.
Antes de testar umfork: registrar apenas capacidades não sensíveis pelo
SDK, conferir linker/reserva e cadeiadeentrada, recusar se inacessível.
SemUnlaunch,semNAND,semfirmware. Se o contrato não for atingido, marcar
essa rotaBLOCKED e manter o fixture/receiver removíveis.
Não pedir NAND,OTP,consoleID,PMK ou senhas para resolver esse gate.

## Próximos experimentos
1. PoC032 cooperativa: códigoB separado, observadorA duranteexecução,
   guards,seqlock e6.000frames emCPU simulado; hardware aindaNOT_RUN.
2. Benchmark diferencial de snapshots/ponteiros/reset contra stockrcheevos.
3. ForkGPL isolado com reserva e loader próprios, sem substituir_nds.
4. Validar o encadeamentoLenny em hardware e homebrew controlado.
5. Captura porframe com erro explícito emoverflow; comparar áudio,input,
   CPU eRAM A/B; nenhuma rede pesada emIRQ.
6. Integrar transporte sódepois:32slots cobrem~0,53s a60Hz, não um atraso
   arbitrário. Se cheio, o monitor de jogos não pode simplesmente pausar
   a captura como faz oprobe032.

## Integração legítima: contrato necessário
rc_client_create recebe callbacks de leitura dememória e server_call.
A leitura retorna quantidade real debytes; região ausente não ézero válido.
server_call é assíncrono e entrega a resposta aocallback oficial.
Login porpassword/token, identify/load porhash oficial, do_frame/idle,
reset/pause e tratamento deconectividade pertencem à sessão doSDK.
HashNintendoDS deve ser feito porrc_hash; nãoMD5 integral doarquivo.
Identificar aROM realmente executada e itsversão/região, não apenasnome.
DTCM é relocável e ARM9 cache exige observador coerente; ponteiros e
alvos devem vir do mesmo snapshot lógico.

Windows proposto:HTTPS validado,User-Agent próprio, token protegido pelo
sistema operacional, nenhum segredo noSD/logs/repositório e nenhum
endpointdeaward alimentado porSIMULATED/replay/diagnóstico.
rc_runtime local de032 não implementa essa sessão. Não habilitar chamadas
deunlock manualmente para fingir integração. A aceitação do cliente e
política deconfiança/hardcore precisam ser verificadas comRA antes da
etapa deenvio; nenhuma aprovação foi solicitada ou obtida aqui.

## Licenças e distribuição
Código novo032 éoriginalMIT. NadaGPL foi copiado para oCoreMIT.
nds-bootstrap eDScheevos sãoGPL-3.0. Adaptação/combinação distribuída
deve manterGPL,avisos efontes correspondentes; separar o componente
GPL de ferramentas MIT não elimina obrigações do componente.
Unicorn é ferramenta de testeGPL, executada fora dos bináriosDSi.
Não é embarcada nos ZIPsSD; os relatórios identificam revisão eSHA.
