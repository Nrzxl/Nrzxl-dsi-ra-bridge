# Current repository

The repository exists at `Nrzxl/Nrzxl-dsi-ra-bridge`, **not** `Nrzxl/dsi-ra-bridge`. The older `gh repo create` instructions below are historical and **should not be executed** on this project. The repository was created public by its owner. ARM `.nds` compilation remains unverified until GitHub Actions produces a build log and binary.

---

# Build atual 0.2.0

Use docs/phase2-checkpoint.md e o workflow arm-diagnostic-manual.yml.
Builds da versão 010 abaixo são histórico; não são instruções da versão 020.

# Compilar e verificar — roteiro preparado, NOT_RUN aqui
O executor desta sessão não estava disponível. Não há comprovante de GCC,
Docker, pacman, linker, ndstool, emulador ou .nds executados.
O script ARM é candidato de build e pode precisar de correção após a primeira
execução; sua existência não é PASS de compilação.

## Diagnóstico ARM no Windows
1. Instale Docker pelo fornecedor oficial, caso queira usar containers.
   Alternativamente use o ambiente devkitPro oficial com a versão clássica
   em instalação isolada, sem substituir uma toolchain de outros projetos.
2. Para o caminho Docker, obtenha deliberadamente a imagem oficial:
   docker pull devkitpro/devkitarm:20241104
3. Revise scripts/build-diag.sh e scripts/Build-Diagnostic.ps1.
4. Em PowerShell 5.1, na raiz do projeto:
   powershell -NoProfile -File .\scripts\Build-Diagnostic.ps1
5. O script resolve o digest instalado, registra pacotes/GCC e compila
   duas vezes no mesmo path interno, com rede desativada e fonte read-only.
6. Se os SHA-256 diferirem ou o build falhar, pare; devolva o erro e logs.
7. Apenas se ambos passarem, o script produz a pasta sd-root e o ZIP
   DSi_RA_Bridge_SD_010_UNVALIDATED.zip em releases/experimental/build-*.

Não foi verificado nesta sessão se essa tag ainda pode ser baixada, nem
seu digest concreto. Não há claim de reprodutibilidade antes dos dois builds.
A versão antiga foi escolhida como experimento isolado, pois os forks
estudados dependem da API clássica. Não desaconselhamos a libnds moderna:
uma porta para Calico será tratada explicitamente, não por troca silenciosa.

## Protocolo e clientes
Node, usando apenas módulos nativos:
node tests/protocol-tests.cjs
node tests/client-tests.cjs
node windows/bridge/bridge.cjs simulate --out SIMULATED.drb
node windows/bridge/bridge.cjs replay --file SIMULATED.drb --log replay.jsonl

Dois terminais, prova de UDP LOCAL, ainda NOT_RUN:
node windows/bridge/bridge.cjs listen --bind 127.0.0.1 --port 18216 --log udp.jsonl
node windows/bridge/bridge.cjs send-sim --host 127.0.0.1 --port 18216
Interrompa o listener com Ctrl+C. Esperado: 120 pacotes source=2.
Isso não testa rádio DSi. Firewall não é alterado.
Para uma futura rede física, usar bind no IP LAN ou 0.0.0.0 de forma explícita.

Alternativa Python 3.8 ou superior, biblioteca padrão:
python windows/bridge/replay.py SIMULATED.drb
Viewer: abrir windows/bridge/viewer.html preservando a árvore de pastas.

## Demonstração rcheevos local, sem autenticação
Com Git, CMake 3.19+ e compilador C instalados:
git clone https://github.com/RetroAchievements/rcheevos.git third_party/rcheevos
git -C third_party/rcheevos checkout --detach 1433173220a7eaede6a9ed7a18e94117be1821e0
cmake -S engine -B build-engine
cmake --build build-engine --config Release
ctest --test-dir build-engine -C Release --output-on-failure

O CMake usa apenas arquivos C do runtime e utilitários, sem executar
scripts de instalação do repositório clonado. O demo deve produzir dois
LOCAL_TEST_TRIGGER e progressão medida. Resultado nesta sessão: NOT_RUN.
Não substitui o cliente rc_client; nenhuma requisição RA é implementada.

## Git experimental
O repositório solicitado não pôde ser localizado/criado daqui.
Depois de revisar os arquivos, em diretório exclusivo, é possível usar:
git init
git add .
git commit -m "Initial diagnostic prototype; ARM and hardware unvalidated"
gh repo create Nrzxl/dsi-ra-bridge --private --source . --remote origin --push
Esses comandos não foram executados. Não usar repo HANNA/SATURN como fallback.
Workflow incluído é manual e só testa protocolo; não publica releases.
