# DSi RA Bridge 0.3.4-K — separar Maxmod de DSWiFi

**Evidência no DSi XL:** J0 BASE (ARM7 oficial Maxmod) abriu com contador LOOP ALIVE; J1 WIFI_CORE (ARM7 oficial DSWiFi+Maxmod) apresentou duas telas brancas. G1 CORE personalizado sem DSWiFi abriu; G2 e H1 com DSWiFi7 falharam.

## Pergunta do 034K

O problema depende de DSWiFi por si só, ou apenas de sua **combinação com Maxmod** (ou do volume de código/memória)? Este diagnóstico usa dois executáveis independentes com o **mesmo ARM9**:
- K0 `DSIRB_034K_MINIMAL.nds`: ARM7 oficial **minimal**, sem DSWiFi e sem Maxmod.
- K1 `DSIRB_034K_WIFI_ONLY.nds`: ARM7 oficial **dswifi**, sem Maxmod.
- J0 e J1 continuam como controles **já testados fisicamente** e foram recompilados de forma inalterada apenas para análise offline dos ELF no CI.
- Estes executáveis NÃO fazem conexão à rede nem sequer inicializam o Wi-Fi no ARM9. Entretanto, o núcleo ARM7 Wi-Fi oficial pode preparar componentes de seu driver durante o boot, motivo pelo qual K1 só deve ser tentado se aprovado o controle K0.

## Teste somente após validar os relatórios CI e o backup SD

1. Desligar o DSi XL totalmente. Fazer backup do SD. Baixar o pacote `DSi_RA_Bridge_034K_OFFICIAL_WIFI_ONLY_SD_ONLY` no Actions; extrair ZIP interno.
2. Copiar **somente** `nds/DSiRABridge_034K` ao SD em `D:\nds\DSiRABridge_034K` (ajustar letra; não substituir `boot.nds`, `private/`, `_nds/`, TWiLight++ ou NAND).
3. No Flipnote Lenny → HBMenu, abrir primeiro `DSIRB_034K_MINIMAL.nds`. Confirmar `MAIN REACHED: YES` e contador `LOOP ALIVE` crescente. START para sair. Se branco, POWER, parar: **NÃO abrir K1**.
4. **Somente se K0 PASS**, abrir `DSIRB_034K_WIFI_ONLY.nds`. Se duas telas brancas, POWER e não repetir. Relatar se MAIN/LOOP apareceu.
5. Nenhuma ROM comercial, configuração Wi-Fi ou tentativa RetroAchievements em qualquer teste.

**Conclusões condicionais:** K0 PASS, K1 WHITE sugere DSWiFi/loader/memória independentes de Maxmod. K0+K1 PASS com J1 WHITE sugere efeito da combinação, layout ou tamanho de DSWiFi+Maxmod; não prova culpado. K0 WHITE põe em dúvida a linha de base de carregamento/arquivo; não continuar.

**Não fazer** Unlaunch, modificações NAND, reinstalação de HBMenu, formatar SD, mexer em cartucho, nem testar 034H GATE, 034G UPDATE, 034F FAT, 034C ou D.

O CI analisa seções estáticas, mas execução física e estabilidade não são provadas por compilação. Conquistas oficiais = 0.
