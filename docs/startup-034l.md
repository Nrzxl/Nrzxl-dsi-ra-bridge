# DSi RA Bridge 0.3.4-L — experimento físico isolado NWRAM, sem Wi-Fi

Com base nos resultados físicos K0/J0 PASS e K1/J1 WHITE, este experimento testa se o aumento da memória DSi-only NWRAM *sozinho* reproduz o branco. O G1 CORE sem DSWiFi já foi confirmado PASS; reutilizamos exatamente a mesma lógica ARM7 básica e uma interface ARM9 idêntica em L0/L1.

Fontes principais:
- https://blocksds.skylyrac.net/docs/internal/memory_map/ — registradores MBK e NWRAM podem depender do loader.
- https://blocksds.skylyrac.net/docs/internal/build_process/ — seções .twl e .twl_bss DSi-only.
- https://blocksds.skylyrac.net/docs/guides/legacy_support/ — limitações de carregadores legados.
- https://blocksds.skylyrac.net/docs/guides/usage_notes/ — núcleos ARM7 e bibliotecas.
- https://blocksds.skylyrac.net/docs/changelog/ — Mbed TLS de ARM7 movido para .twl em 1.15.1.

L0 DSIRB_034L_CONTROL.nds: ARM7 skeleton do G1 e interface com MAIN REACHED: YES + LOOP ALIVE, sem rede.
L1 DSIRB_034L_PAD.nds: igual L0, mas ARM7 reserva padding inerte .twl (+17844 bytes) e .twl_bss (+13300 bytes), para aproximar o footprint da biblioteca DSWiFi7. Dados são inertes; referência de endereços apenas para retenção pelo linker.

Os programas NÃO carregam jogos, não montam/escrevem SD, não acessam Wi-Fi, não alteram SCFG/MBK, NAND, Unlaunch nem boot.nds. São ferramentas de observação e podem travar na tela branca; não há garantia de compatibilidade.

**Procedimento:** DSi desligado e SD com backup previamente conferido. Baixar artefato DSIRB_034L_NWRAM_PAD_SD_ONLY do GitHub Actions; extrair ZIP interior; copiar **somente** pasta nds/DSiRABridge_034L para D:\nds\DSiRABridge_034L (ajustar letra). Não substituir boot.nds, private/, _nds/ nem TWiLight++.

Testar PRIMEIRO DSIRB_034L_CONTROL.nds (L0) em Flipnote Lenny → HBMenu. Deve mostrar MAIN REACHED: YES e LOOP ALIVE avançando. START para sair. Se branco, desligar pelo POWER e NÃO testar L1.

APENAS se L0 PASS, abrir DSIRB_034L_PAD.nds (L1). Se exibir os mesmos textos e contador, PASS. Se branco, POWER e PARAR. Não repetir automaticamente e não abrir arquivos 034C/D/F3/G3/H2/J1/K1.

**Interpretação cautelosa:** L0 PASS + L1 PASS aponta que aumentar o footprint NWRAM isoladamente não é suficiente para reproduzir branco; investigar código/inicialização específica de DSWiFi ou loader. L0 PASS + L1 WHITE favorece problema em carga/zero de .twl/.twl_bss ou mapeamento NWRAM, mas não o prova. L0 WHITE exige revisar regressão de carregamento, SD e headers.

CI PASS somente valida binários; hardware L0/L1 NOT_RUN até teste físico. RA awards 0 e retail monitoring não comprovado.