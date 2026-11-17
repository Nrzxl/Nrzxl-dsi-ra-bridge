# DSi RA Bridge 0.3.4 — caminho retail, primeiro gate somente leitura

**Status:** DESIGN + PREFLIGHT IMPLEMENTADOS; monitor retail **NOT_IMPLEMENTED**; teste real 0.3.4 no DSi XL **NOT_RUN**.
**Base imutável:** 0.3.3 `2529214498aaefea5d9ec5c281165b0f02eb341e`. Evidência física da fixture 033: [Issue #1](https://github.com/Nrzxl/Nrzxl-dsi-ra-bridge/issues/1).
**PEER TIMEOUT 032:** OPEN. Sem Release, merge, modificação do SD, NAND, Unlaunch ou nds-bootstrap estável.

## Gate 034-A: triagem local de imagem DS

`scripts/retail_preflight_034.py` inspeciona **somente leitura** uma cópia legítima de jogo `.nds` **na máquina do proprietário** (não enviar/commitar ROM).
Executar em Python 3.10+:

```powershell
python scripts/retail_preflight_034.py "C:\JOGOS\COPIA_ORIGINAL.nds"
```

Opcionalmente, se o executável de hash 0.3.3 estiver localmente disponível:

```powershell
python scripts/retail_preflight_034.py "C:\JOGOS\COPIA_ORIGINAL.nds" --hash-tool "C:\DSIRB\dsirb_nds_hash.exe"
```

O utilitário verifica tamanho, unit code, CRC16 do cabeçalho, limites de seções ARM9/ARM7/(ARM9i/ARM7i quando declaradas), entrypoints, alinhamento, sobreposição de seções no arquivo e banner mínimo.
Não tenta autenticar a imagem, validar overlays, mapear toda a RAM ou provar compatibilidade. Header/CRC legítimos **não são** prova de origem legítima ou execução segura. O status de sucesso é deliberadamente `STRUCTURE_PASS_RETAIL_MONITOR_NOT_PROVEN` e `retail_monitor_ready=false`.

A opção `--hash-tool` chama um **binário local confiável da própria build** da 0.3.3, já revisado; o hash usa `rc_hash_generate_from_file` de rcheevos com `RC_CONSOLE_NINTENDO_DS`. Esse hash não é MD5 do arquivo inteiro, não resolve o título online, não faz login e não solicita conquistas. Nunca usar o executável em arquivos instrumentados. A opção é dispensável.

Testes sintéticos sem ROM: `python tests/retail_preflight_034.py` (9 testes). A CI replica Linux e Windows, sem SDK ARM, emulador, ROM, credenciais, upload ou rede.

## Gate 034-B: observar jogo retail real (AINDA NÃO IMPLEMENTADO)

A prova da fixture 033 foi obtida porque B **já estava instrumentado** antes de iniciar. Isto **não** prova que o observer de A permanece vivo após chainload genérico; o nds-bootloader limpa e reinicializa ARM7/RAM/cache/IRQs.

Proposta técnica para revisão:
1. Construir variante **GPL separada** do fork nds-bootstrap/DScheevos (revisões auditadas no `docs/research-independent-033.md`), sem substituir arquivos da instalação estável. Não transplantar código GPL para módulo MIT.
2. Primeiro medir, em um homebrew aberto ou fixture própria, as permissões reais Flipnote Lenny → HBMenu → loader, incluindo modo DSi, SD interno, SCFG/MBK/SDIO e arm7/arm9; não presumir elevação e não escrever NAND.
3. Reservar região de monitor por projeto de carregamento, não por aposta em RAM ociosa. Auditar cache de ROM, heap/BSS, TWL/overlays, MPU/cache, pilha própria e IRQ/OS_Halt; faixa 0x02200000–0x02220000 vale **somente** para a fixture 033. Não aplicar patcher `instrument-fixture-033.py` em jogos.
4. Com cópia de jogo legitimamente obtida, comparar dump/estado real por frame incluindo main RAM, DTCM de CP15 e ponteiros dinâmicos, no Windows com rcheevos; rejeitar frames faltantes em vez de fabricar continuidade.
5. Validar estabilidade de save, áudio, controles, desempenho e rede real. A captura do 033 registra 0 scanlines como resolução grosseira, **não** custo CPU zero.
6. Somente após compatibilidade e revisão por RetroAchievements projetar hash/sessão HTTPS/login (credenciais locais no Windows), desbloqueio oficial e regras softcore/hardcore. Zero achievements oficiais no 0.3.4-A.

## Limites de manutenção

- Versões 0.2.0, 0.3.0, 0.3.1, 0.3.2 e 0.3.3 intocadas.
- Nenhuma publicação de ROMs, saves, NAND, OTP, console ID, tokens, IPs/logs privados ou a captura física bruta.
- Independente da validação 034-A, `PEER TIMEOUT` 032 permanece uma investigação paralela; não use envio de ACK como prova de READY.
- Não copiar nenhum arquivo da branch 034 no DSi até existir pacote isolado + aprovação de build e teste físico documentados.

### Critério de conclusão do gate 034-A

Código e testes passando; inspeção de arquivo local é estritamente não destrutiva, rejeita entradas inválidas e informa explicitamente `retail_monitor_ready=false`. Este critério **não conclui** o gate 034-B.
