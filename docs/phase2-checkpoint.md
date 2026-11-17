# Fase 2 — código preparado; compilação real bloqueada
## Base recuperada
Os 33 fontes foram recuperados do DSi_RA_Bridge_010_Source.ps1.txt fornecido.
O ZIP mais recente foi localizado, mas não pôde ser extraído sem executor.
Portanto, não afirmamos ter auditado mudanças adicionais dentro desse ZIP.
O original e a instalação do usuário permanecem intactos.

O texto anexado da Fase 2 registra 120 pacotes UDP locais, replay Node/Python
e sintaxe C com mocks como checkpoint de outro ambiente. São evidências
anteriores informadas, não resultados repetidos nesta sessão.

## Alterações desta etapa
- Alvo e diretório exclusivos 020; protocolo DSRB v1 preservado.
- .DEFAULT_GOAL explícito, título identificável e normalização de paths GCC.
- APIs clássicas de timers conferidas no fonte libnds v1.8.0.
- Script detecta dkp-pacman ou pacman e registra inventário/ds_rules.
- Sem atualização de pacotes dentro do container: a imagem oficial já os contém.
- Build candidato recusa silenciosa mistura com libnds 2.x/Calico.
- Workflow manual usa checkout do SHA exato e actions oficiais fixadas por SHA.
- Dois containers isolados usam o mesmo digest e o mesmo path /work.
- Validação do cabeçalho, CRC16, ARM9/ARM7, ranges e ELF ARM.
- Empacotamento só depois de NDS validado, SHA coincidente e dois builds iguais.
- Pacote SD tem diretório próprio; nenhum boot.nds/private/ é incluído.
- Logs são enviados como artefatos mesmo se o build falhar.
- Nenhuma chamada RA ou alteração de loader estável.

A validação estrutural é uma política para este diagnóstico, não um parser
universal de ROMs nem uma prova de compatibilidade física. Os testes sintéticos
existem somente em memória e não geram executáveis .nds.

## Estados desta sessão
| Verificação | Estado | Evidência |
|---|---|---|
| Recuperação do script | PASS | 33 entradas JSON lidas |
| Protocolo | PASS | 632 verificações reexecutadas em V8 |
| Cliente com arquivos em memória | PASS | 7 verificações reexecutadas em V8 |
| Novo validador NDS | PASS | 25 verificações com cabeçalhos sintéticos |
| Node/Python reais e UDP | NOT_RUN | Sem executor |
| Compilação C/ARM e ELF real | BLOCKED | Executor indisponível |
| GitHub repository | BLOCKED | Nrzxl/dsi-ra-bridge retornou 404 |
| Criação remota do repository | BLOCKED | Ferramenta não oferece create-repository |
| Workflow GitHub Actions | NOT_RUN | Preparado; sem repository acessível |
| ZIP de fontes local | BLOCKED | Sem filesystem |
| .nds e ZIP para SD | BLOCKED | Dependem do build ARM |
| Emulador e DSi físico | NOT_RUN | Não executados |
| Monitor/conquistas oficiais | NOT_RUN | Fora do teste desta fase |

Total: 664 verificações JavaScript, com escopos diferentes.
As 632 do protocolo incluem uma sequência de 600 casos; não são testes
independentes de hardware. Nenhum hash de binário é informado porque ele
ainda não existe.

## Desbloquear o caminho remoto
1. Recuperar os fontes 020 em uma pasta NOVA pelo inicializador entregue.
2. Instalar Git/GitHub CLI pelo fornecedor oficial, se ausentes, e autenticar
   a conta Nrzxl. Nenhuma credencial deve ser colada neste chat.
3. Na pasta do projeto, criar e subir um repository separado e privado:
   git init -b main
   git add .
   git commit -m "Prepare diagnostic 020 ARM pipeline; hardware unvalidated"
   gh repo create Nrzxl/dsi-ra-bridge --private --source . --remote origin --push
4. Criar a branch experimental:
   git switch -c feat/dsi-ra-bridge-diagnostic-build-020
   git push -u origin feat/dsi-ra-bridge-diagnostic-build-020
5. O workflow_dispatch precisa existir na branch default para aparecer no
   menu Actions. A carga inicial acima coloca o workflow em main.
6. Executar manualmente na branch:
   gh workflow run arm-diagnostic-manual.yml --ref feat/dsi-ra-bridge-diagnostic-build-020
7. Devolver o link da execução. A inspeção dos logs e a correção podem então
   continuar pela conexão GitHub, dentro das suas capacidades.

Os comandos acima não foram executados aqui. Se o repository já existir,
não usar create de novo; conectar apenas após confirmar proprietário,
visibilidade e conteúdo. Não usar HANNA/SATURN como fallback.
O workflow não publica releases nem altera visibilidade. Cobrança/minutos
do GitHub podem impedir uma execução privada; isso é falha do runner,
não falha de compilação. Não tornar público automaticamente.

## Caminho local alternativo
Com Git, Docker, Node e Python instalados e fontes commitidos:
docker pull devkitpro/devkitarm:20241104
powershell -NoProfile -File .\scripts\Build-Diagnostic.ps1
O pull é explícito; o script não instala nada. O pacote só será produzido
se todos os gates passarem. A tag é resolvida em digest e registrada.

## Fontes adicionais consultadas
https://github.com/devkitPro/libnds/blob/v1.8.0/source/common/timers.c
https://github.com/devkitPro/libnds/blob/v1.8.0/source/common/libnds_exit.arm.c
https://github.com/devkitPro/libfat/blob/master/source/libfat.c
https://github.com/devkitPro/libfat/blob/master/source/disc.c
https://github.com/devkitPro/ndstool/blob/76e8b681bb225d945a48852821e03114e6c7ce1c/source/header.h
https://github.com/devkitPro/ndstool/blob/76e8b681bb225d945a48852821e03114e6c7ce1c/source/ndscreate.cpp
https://github.com/devkitPro/docker/blob/5f17e228f1f67c7cfb481ae658512aa072d584a1/devkitarm/Dockerfile
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
