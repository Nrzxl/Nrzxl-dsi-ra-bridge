# Estado atual
Consulte docs/phase2-checkpoint.md para a Fase 2. O restante é histórico da 010.

# Validação em 16/11/2026
## Executado
PASS: inspeção dos arquivos e metadados dos seis projetos requeridos.
Essa é evidência de pesquisa, não reprodução dos testes de terceiros.
PASS: protocolo JavaScript em V8, 632 verificações.
Escopo: CRC, layout, limites, sequência, origem marcada e trace simulado.

FAIL: primeira execução da suíte, falta de TextEncoder na bancada V8.
CORRIGIDO: vetor de bytes literal no teste; nova execução PASS.

## Bloqueado
BLOCKED: execução local de shell e criação de arquivos por apply_patch.
Erro real: No usable execution environment is available.
Consequências: não instalar toolchain, clonar, compilar ARM, gerar map,
medir tamanho/custo real, usar emulador ou construir ZIP local.

BLOCKED: repositório remoto Nrzxl/dsi-ra-bridge.
Consulta retornou 404. A ferramenta conectada não oferece create-repository.
Não foi criada branch em outro projeto como desvio.

## Não executado
NOT_RUN: código C/ARM, memória física do DSi, libfat, Node/Python Windows,
browser viewer, UDP real, rcheevos C, bootstrap patch, TLS/autenticação RA,
avaliação de sets reais e desbloqueios oficiais.
Sem SHA-256 de .nds porque nenhum .nds foi produzido.

## Entrega concreta e limites
Fontes do diagnóstico, protocolo testado, clientes, demo rcheevos,
scripts de build e documentação estão no pacote recuperável.
O inicializador só escreve uma nova pasta local. Não compila ou instala.
O ZIP para SD é saída futura do build, condicionado a sucesso e
comparação dos binários; não é um arquivo já entregue.

Nenhuma mudança no console ou em HANNA/SATURN foi realizada.

PASS adicional: 7 verificações do CLI JavaScript real com filesystem em memória: geração/replay de 600 registros, origem, CRC, truncamento e recusa de sobrescrita. Não é teste de filesystem Windows ou sockets. O adaptador de teste precisou remover o shebang antes de avaliar o código em V8; a execução corrigida passou.
