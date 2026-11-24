# DSi RA Bridge — 0.4.7: condições locais + capturador C (laboratório PC)

**STATUS INICIAL:** branch QA isolada; sem novo `.nds`, sem instalação no DSi, sem sessão RetroAchievements, sem ROM, sem rede, sem autenticação, **sem desbloqueios oficiais**. A 0.4.4 permanece como referência física de RAM; 0.4.5 catalogou **157/157 metadados** do jogo oficial RA #9983; 0.4.6 concluiu o primeiro protocolo sintético DR46. DSi XL continua sem Unlaunch/NAND modificada.

## Qual foi o avanço

A 0.4.6 executava `rc_runtime` real em cima de uma planilha CSV com estrelas/moedas inventadas. A 0.4.7 faz o motor do **mesmo rcheevos C pinado**, commit `754965ef28db22b0411bfccbde39154cd09e6b79`, ler **diretamente os pacotes binários de memória DR46-v1**. A avaliação, portanto, usa as regiões do snapshot (RAM principal e DTCM lógica) e o callback de memória; se faltar qualquer byte solicitado por uma condição, **a reprodução é bloqueada**.

O código **também pode receber definições reais de conquistas**, caso o usuário as tenha obtido por meios autorizados: `prepare-local-conditions-047.py` aceita um patch privado local, valida IDs do RA #9983 contra o catálogo sanitizado da 0.4.5 e produz um manifest **privado** com condições originais para `rc_runtime_activate_achievement`. Isso é somente um **caminho de entrada local**: **não importamos nem testamos as 157 definições reais**, e não buscamos material autenticado por métodos alternativos. MD5s no campo `MemAddr` da API pública são recusados.

Outro componente, `lab/dr46-capture-047.c/.h`, oferece um **codificador portável candidato ao ARM9**: recebe uma watchlist ordenada, um callback de leitura e um identificador de frame e gera o mesmo pacote CRC32 do Python. Sem código de hardware, detour, hook, socket, autenticação, escrita de memória ou alteração de NAND. Comparamos **byte a byte** o resultado C contra o protocolo Python. **Isso não é captura física implementada.**

## Recursos implementados

| Arquivo | Finalidade |
| --- | --- |
| `scripts/prepare-local-conditions-047.py` | Importa patch de condições **já autorizado e local**, rejeita IDs errados, duplicados, digests MD5 ou texto malformado; valida correspondência com catálogo 045; gera um TSV privado. Também tem fixture sintética independente, para testes sem patch real |
| `lab/ra-frame-replay-047.c` | Interpreta stream binário DR46, valida CRC, sequência, frame, sessão, jogo, regiões; chama `rc_runtime_do_frame` com bytes *do mesmo frame*; conta eventos locais, nunca envia awards |
| `lab/dr46-capture-047.c` / `.h` | C portátil sem dependência zlib, codifica snapshots de endereços de uma watchlist via callback de leitura (sem acesso real ARM9 nesta etapa) |
| `lab/test-dr46-capture-047.c` | Testes locais de callback incompleto, watchlist sobreposta e igualdade do pacote |
| `tests/test-local-conditions-047.py` | Testes da validação do patch, catálogo, permissões de arquivo, ausência de condições nos logs |
| `.github/workflows/conditions-and-capture-047.yml` | Linux: runtime C real, paridade C/Python, falhas por CRC/frames/RAM; Windows PowerShell 5.1: scripts e regressões; **apenas dados sintéticos** |

## Como testar no Windows sem credenciais e sem jogo

Baixe o pacote da ação 047 após a CI passar; extraia o ZIP para uma pasta, abra nela o PowerShell:

```powershell
py -3 .\tests\test-local-conditions-047.py
py -3 .\tests\test-frame-bridge-046.py
py -3 .\scripts\prepare-local-conditions-047.py --synthetic --out "$env:USERPROFILE\Downloads\RA_047_synthetic_conditions.tsv"
py -3 .\scripts\frame-bridge-046.py demo --out "$env:USERPROFILE\Downloads\RA_047_synthetic_frames"
py -3 .\scripts\frame-bridge-046.py verify --input "$env:USERPROFILE\Downloads\RA_047_synthetic_frames\synthetic-frames-046.bin"
```

**Atenção:** o teste cria arquivos novos e se recusa a sobrescrevê-los. Repetições devem escolher outros nomes. Compilação do código C do rcheevos é validada na CI Linux; o ZIP inclui fontes e binário Linux do replay, não um programa C nativo do Windows e não um `.nds`.

## Importação real (somente quando houver patch de origem autorizada)

**Não coloque a Web API Key, ROM, patch autenticado ou manifest privado no GitHub/ChatGPT.** No seu próprio computador, utilizando o **catálogo de cobertura 045** que você já gerou:

```powershell
py -3 .\scripts\prepare-local-conditions-047.py --catalog "$env:USERPROFILE\Downloads\RA_9983_coverage_045_20261123_134728.json" --authorized-patch "C:\CAMINHO_PRIVADO\patch9983.json" --require-all --out "$env:USERPROFILE\Downloads\RA_9983_triggers_PRIVADO_047.tsv"
```

Esse comando não busca um patch. Ele o processa **apenas se já existir uma cópia legitimamente acessível ao usuário**. O manifesto contém **lógica integral em texto puro**, não é um relatório sanitizado. Não compartilhe nem anexe. O sistema não sabe ainda se um patch real completo está disponível ou se os 157 são todos elegíveis na mesma sessão. Uma definição recente incompatível com o pin do `rcheevos` provocará falha de ativação até atualização/adaptação aprovada.

Importante: executar condições verdadeiras requer também **frames genuínos do jogo** com todos os endereços lidos por essas condições em cada frame; o arquivo 046 sintético não tem esses dados. O laboratório não permite inventar desbloqueios. A partir de um patch real e uma watchlist correta, a avaliação é local, com `rc_runtime_do_frame` por frame, eventos de teste no terminal e **nenhuma rede RA**.

## Protocolo, limitações e riscos

- Pacote DR46 v1 da 046: sessão 16B não nula, hash RA ASMP EU, sequência u32, frame u32, CRC32 e até 32 regiões contíguas/sorteadas; payload até 1024B. Header 52B + CRC 4B; stream é prefixado pelo comprimento u16. Em 60 fps, a carga teórica máxima do wire sem prefixo é aproximadamente 65KiB/s; **não medimos throughput Wi-Fi real, latência ou desempenho físico**.
- `rc_runtime` é uma biblioteca **de avaliação local**, não substitui `rc_client` para login, identificação, sessão, conexão ou compliance. **Nenhuma sessão/award oficial foi executado.**
- Falta de amostra, salto de frame, CRC inválido, sessão diferente ou memória solicitada ausente abortam a reprodução. O código C puro `dr46_capture_encode` recusa leituras incompletas **antes de entregar um pacote completo**; o chamador futuro deve descartar a saída caso retorne tamanho zero.
- Ao usar arquivo local genuíno, **CRC32 não prova autenticidade**. A proteção final contra ataques/replay, as condições de uso do RA, a precisão do ARM9 e o anti-cheat ainda exigem investigação e autorização.
- Condições com endereços indiretos, DTCM, Delta, contadores, modificadores temporais ou intervalos não contíguos podem demandar watchlist dinâmica/expansão. Não é possível garantir que os 157 triggers cabem no orçamento de 1KiB/frame. **É um limite temporário de laboratório**, não promessa de cobertura.
- **Zero validação física 047**: o código do capturador ainda não foi inserido no DScheevos nem conectado a um callback ARM9 real; não instalaremos nada na SD para executar este gate.
- Congelamentos, interferência no áudio, IRQ/VBlank, vídeo e saves são critérios de QA da próxima PoC física. O bug de áudio do menu continua OPEN, sem regressão forçada.

## Próximos gates

1. Obter conjunto completo de condições RA #9983 via um fluxo cliente legítimo, ou um patch já autorizado, mantendo credenciais/definições locais. Verificar revisão do conjunto e compatibilidade sintática com o pin usado.
2. Validar mapeamento de endereço/pointer da variante ASMP Europa em um emulador com depuração, coletar frames reais de maneira consentida e medir % de memória disponível para o conjunto.
3. Adicionar adaptador ARM9 real do DR46 em branch isolada, com buffer circular pequeno, medição de VBlank/IRQ e taxa de perda. Não ativar prêmios.
4. Só após CI + revisão do desempenho, criar pacote SD-reserva e testar hardware; manter a 0.4.4 intacta.
5. Confirmar com administração RA os requisitos de cliente de hardware original antes de qualquer envio de awards.

Documentação: https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration e https://github.com/RetroAchievements/rcheevos/wiki/rc_runtime_do_frame

**Critério de sucesso desta entrega:** QA do protocolo C/host e do loader local, não desbloqueios oficiais.
