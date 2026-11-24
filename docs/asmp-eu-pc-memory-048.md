# DSi RA Bridge — 0.4.8: laboratório de RAM real do Mario europeu (ASMP)

**Estado:** ferramenta de PC. Sem novo .nds, sem alteração no DSi, SD/NAND, ROMs ou saves e sem submissão de conquistas.

A 0.4.4 validou leitura dinâmica de RAM no DSi XL; 0.4.5 catalogou 157 conquistas RA do jogo 9983, mas **não** condições executáveis. A 0.4.6–0.4.7 executou uma prova de conceito de ponte de RAM/rc_runtime apenas **sintética**. A 0.4.8 permite obter RAM real a partir do BizHawk com núcleo melonDS, sem precisar usar fisicamente o DSi.

## Evidência externa pesquisada — NÃO confundir versão EU com USA

A documentação técnica de Skelux para **Super Mario 64 DS (EU)** registra estes endereços ARM9. São **pistas publicadas, ainda não confirmadas na nossa ROM ASMP pelo laboratório**:

| Endereço ARM9 | Offset RA (Main RAM) | Hipótese |
| --- | --- | --- |
| 0x0209F2F4 | 0x09F2F4 | Vidas |
| 0x0211117C | 0x11117C | Saúde — pode exigir ponteiro/estrutura |
| 0x02092144 | 0x092144 | Saúde — pode exigir ponteiro/estrutura |
| 0x0209F2F8 | 0x09F2F8 | ID de fase |

Fonte: https://hack64.net/wiki/doku.php?id=super_mario_64_ds:skelux_documentation_eu .

A lista TASVideos https://tasvideos.org/GameResources/DS/SuperMario64DS documenta moedas em 0x02097454 e vidas em 0x020973EC, **mas especificamente para USA v1.0**. Esses números não são automaticamente válidos para ASMP europeu. Localizar estrelas, moedas, tempo, minigames e flags permanentes **continua pendente**.

## Procedimento para obter memória REAL no seu Windows

**Pré-requisitos:** BizHawk/EmuHawk com núcleo melonDS, sua própria ROM legítima europeia ASMP (mantida apenas no PC) e Python 3. Não enviar ROM, save, BIOS ou chaves a ninguém.

1. Inicie BizHawk, carregue a sua ROM ASMP e navegue até um local estável com pelo menos uma moeda por perto. Durante os testes, deixe o sistema de conquistas do próprio emulador desligado para não gerar sessões/desbloqueios involuntários.
2. Abra **Tools → Lua Console → Open Script** e selecione o arquivo **lab/bizhawk-asmp-eu-capture-048.lua** deste projeto. A janela oferece os botões **1. BEFORE**, **2. IDLE**, **3. AFTER**.
3. **Pause** o emulador; clique **BEFORE** para capturar 4 MiB de RAM antes do evento.
4. Retome sem pegar moeda nem mudar significativamente de cena; aguarde alguns segundos, pause e clique **IDLE**. Essa é a captura de controle (para eliminar timers/RNG que já mudavam naturalmente).
5. Retome, **pegue exatamente uma moeda**, pause e clique **AFTER**.
6. O Lua cria em Downloads três dumps PRIVADOS de RAM (.bin com 4 MiB cada) e três arquivos .json com frame, domínio e verificação de cabeçalho. O script recusa se o frame avançar durante uma captura. **Esses dumps .bin são confidenciais para diagnóstico; não enviar, não dar commit, não publicar**.
7. No PowerShell aberto na pasta do projeto que contém scripts, use o prefixo exato exibido pelo script Lua no console, substituindo o exemplo de data/frame:

```powershell
$base = "$env:USERPROFILE\Downloads\DSi048_ASMP_AAAAMMDD_HHMMSS_12345"
py -3 .\scripts\analyze-asmp-ram-048.py --before ($base + "_before.bin") --idle ($base + "_idle.bin") --after ($base + "_after.bin") --event coin_up --rom "E:\CAMINHO_PRIVADO\Super Mario 64 DS Europe.nds" --out "$env:USERPROFILE\Downloads\DSi048_coin_candidates.json"
```

### Forma mais fácil no Windows — assistente PowerShell 5.1

Depois de obter as três capturas, em vez de digitar os três nomes de arquivo, abra um PowerShell **na pasta raiz extraída que contém scripts** e execute:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-MarioRAM-048.ps1 -Event coin_up -RomPath "E:\CAMINHO_PRIVADO\Super Mario 64 DS Europe.nds"
```


O assistente procura automaticamente em Downloads o conjunto **BEFORE** mais recente, confere se existem **IDLE** e **AFTER** da mesma sessão, compara as capturas e grava um novo JSON sanitizado com o caminho exibido no console. **Não copia nem envia a ROM**.

Se seu terminal estiver **dentro da pasta scripts**, execute sem repetir o diretório:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Invoke-MarioRAM-048.ps1 -Event coin_up -RomPath "E:\CAMINHO_PRIVADO\Super Mario 64 DS Europe.nds"
```


Caso o emulador não consiga exibir cabeçalho e você não tenha a ROM homologada localmente, a opção **-AllowUnverifiedHeader** permite gerar relatório explicitamente **não verificado**. É preferível usar **-RomPath** para confirmar o hash do arquivo ASMP Europa.

O argumento **--rom** confirma **localmente** o hash RA Nintendo DS usando a função já aprovada na 0.4.4 (hash esperado: ba3c4052e00c5cc31df5d5534c39de1b). Ele não envia a ROM à rede. Verifica o *arquivo fornecido*, não prova que o emulador estava rodando aquele mesmo arquivo. Se o script não conseguir ler o cabeçalho do cartucho no domínio ROM e você não apontar um arquivo para --rom, o analisador bloqueia por padrão. Para uma investigação marcada explicitamente como **não verificada**, use **--allow-unverified-header**.

O resultado será **somente** um JSON sanitizado com offsets, larguras de 1/2/4 bytes, antes/depois, ranking e flags de incerteza. **Envie apenas o DSi048_coin_candidates.json, nunca os .bin/ROM**.

Repita uma nova tripla BEFORE/IDLE/AFTER para:
- **--event life_down**: perder exatamente uma vida.
- **--event star_up**: receber uma Power Star.
- **--event health_down**: sofrer dano sem perder a vida.
- **--event level_change**: entrar em outra fase (pode causar milhares de mudanças; maior risco de falsos positivos).

**Três repetições independentes** de cada evento são preferíveis antes de declarar qualquer endereço confirmado. Em especial, Star e Health podem depender de flags/ponteiros, não de um contador que sobe ou desce uma unidade.

## Teste sintético — sem ROM, sem emulador, sem DSi

```powershell
py -3 .\tests\test-asmp-ram-048.py
py -3 .\scripts\synthetic-asmp-captures-048.py --out "$env:USERPROFILE\Downloads\DSi048_SYNTHETIC"
$base = "$env:USERPROFILE\Downloads\DSi048_SYNTHETIC\DSi048_SYNTHETIC_GAME_UNVERIFIED"
py -3 .\scripts\analyze-asmp-ram-048.py --before ($base + "_before.bin") --idle ($base + "_idle.bin") --after ($base + "_after.bin") --event coin_up --allow-unverified-header --out "$env:USERPROFILE\Downloads\DSi048_SYNTHETIC_REPORT.json"
```


O teste não fornece evidência de nenhum endereço Mario: o valor de moeda e a ROM são **sintéticos/não verificados**.

## Garantias e limites

- O Lua faz somente leitura de memória **Main RAM** do núcleo melonDS em modo DS, que precisa expor 4 MiB. Nenhuma escrita, cheat, salvamento, modificação de jogo, NAND ou rede.
- Se o núcleo expõe um domínio ROM cujo cabeçalho tenha código ASMP, o Lua registra **HEADER_MATCH_ONLY**, não um hash RA validado. Se não, registra **UNVERIFIED** e o Python exige confirmação explícita ou um caminho de ROM com hash correto.
- Os arquivos gerados são snapshots MANUAIS do emulador, não amostras de hardware sincronizadas a 60Hz. Verificar que o contador de frames não avançou reduz inconsistência, mas não é prova formal de atomicidade.
- A heurística de diferença de RAM ignora bytes que já mudaram entre BEFORE e IDLE. Essa técnica reduz ruído, mas não confirma causalidade nem equivalência com lógica RA.
- Relatórios não contêm dumps nem strings de condições autenticadas. Evite compartilhar dumps ou ROMs.
- Não usamos nenhuma das **157 condições executáveis reais** até agora; a 0.4.7 ainda só possui interface local para definições obtidas legitimamente.
- A 0.4.4 continua preservada e o áudio intermitente ao abrir menu permanece pendente.

## Fontes

- BizHawk API Lua: https://tasvideos.org/Bizhawk/LuaFunctions
- Suporte RA a Nintendo DS via BizHawk/melonDS: https://docs.retroachievements.org/general/emulator-support-and-issues.html
- Desenvolvimento de conquistas: https://docs.retroachievements.org/developer-docs/emulator-setup-for-developers.html
- RAM documentada para ASMP Europa: https://hack64.net/wiki/doku.php?id=super_mario_64_ds:skelux_documentation_eu
- RAM documentada USA v1.0 (não intercambiável com EU): https://tasvideos.org/GameResources/DS/SuperMario64DS
