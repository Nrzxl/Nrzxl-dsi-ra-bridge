# PoC residente032 — pacote separado, não atualizar bootstrap
**HardwareNOT_RUN.** Primeiro teste disponível é CPU ARM946 em simulação,
não boot completo DS/DSi. Veja o resultado real no Actions antes de usar.

ProgramaA é um NDS próprio com monitorVBlank. Ele carrega um binárioB
cooperativo separado (payload.dsb) numa alocação própria alinhada, valida
tamanho<=4096,headerABI eCRC, limpaD-cache e invalidaI-cache daquela faixa
e chama B. B executa seu próprio loop ARM e altera estado controlado.
Enquanto B ocupa o fluxo principal, o handlerA permanece residente e
registra memória a cadaVBlank. A interrompe B após600frames e volta ao menu.

B é um módulo ARM sem imports, dados absolutos, BSS ou relocations.
**Não é um segundo NDS independente**, não reiniciaARM7/MPU e não é jogo.
A PoC exercita execução de código separado com observador ativo; não
demonstra persistência através de um loaderNDS genérico ou jogo comercial.
Isso exige integração com o carregador e reserva antes do startup do jogo.
Não há hooks em TWiLight, nds-bootstrap, memória de jogo ou instalaçãoestável.

Simulação: Unicorn2.1.4 oficial, arquivo release verificado porSHA256,
modeloARM946. B é o código de máquina real compilado por devkitARM.
Um observador de frames simulado usa o MESMO leitor C deA. Executa6000
frames em duas bases de carga distintas para testar independência de posição.
É modeloCPU com framehook host; não simulaIRQ/MPU/cache/timing doDSi,
DS BIOS, áudio,SD ou rede. O NDS deA é compilado/validado, mas não é bootado
pelo testeCPU. Não confundir PASS desse fixture com funcionamento físico.

Estado usa geração par/ímpar: cópia durante publicação é rejeitada, nunca
aceita como amostra válida. CSV registra contagem e leituras rejeitadas,
não inventa continuidade perfeita. Guards e checksum validam dados deB.
Leitura restrita ao struct próprio, sem DTCM/ponteiros de terceiros.
UsoRAM conhecido:600x32=19200B de registros,estado40B,code<=4096B+SDK.
Ticks medem só leitura do monitor; não representam todo custo deIRQ.
Áudio e controles de jogo:NOT_RUN, pois não há jogo nem áudio nestaPoC.

Roteiro físico posterior, separado do transporte:
- Faça backup; extraia o ZIPPoC numa pasta doPC para conferir hashes.
- Caso aprove testar estaPoC, adicione apenas nds/DSiRABridge_032_Resident
  e DSiRABridge_032_Resident/payload.dsb aoSD. Não copie para_nds.
- Abra o NDSResident peloHBMenu. A carregaB. Retorno automático~10s.
  START duranteB pedeaborto pelo handler próprio. X apósretorno salva
  POCnnn.csv porO_EXCL. Não removerSD atéarquivo fechado.
- Registre frames,valid,rejected,max ticks,foto eCSV.
- O pacote é removível pelas duas novaspastas; versõesanteriores preservadas.

A meta final continua jogos eRA. O caminho recomendado pararetail é avaliar
um forkDScheevos GPL isolado; oBridge complementa comtelemetria eoráculo
rcheevosWindows. EstaPoC própria reduz uma incerteza pequena sem prometer
ser a arquitetura definitiva debootstrap.
