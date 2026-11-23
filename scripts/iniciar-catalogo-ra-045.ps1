<#
.SYNOPSIS
  DSi RA Bridge 0.4.5 - importar catálogo oficial do Super Mario 64 DS.
.DESCRIPTION
  Compatível com Windows PowerShell 5.1. Executa o importador Python já
  auditado no mesmo repositório. Solicita a Web API Key em entrada oculta,
  usa-a somente no processo atual e a remove em finally.
  Não envia dados para o GitHub, não modifica SD, ROM, save ou NAND.
  A API oficial recebe a chave via HTTPS, conforme o protocolo do RA.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\iniciar-catalogo-ra-045.ps1
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\iniciar-catalogo-ra-045.ps1 -MetadataFile .\fixtures\game-9983.json
#>
[CmdletBinding()]
param(
    [string]$MetadataFile,
    [string]$OutputFile
)

Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'ra-set-coverage-045.py'
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    throw "Importador ausente. Execute na pasta do projeto, com o arquivo ra-set-coverage-045.py ao lado."
}

if (-not $OutputFile) {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $OutputFile = Join-Path ([Environment]::GetFolderPath('UserProfile')) ("Downloads\RA_9983_coverage_045_" + $stamp + ".json")
}
$OutputFile = [IO.Path]::GetFullPath($OutputFile)
if (Test-Path -LiteralPath $OutputFile) {
    throw "O relatorio ja existe; nao vou sobrescrever: $OutputFile"
}
$folder = Split-Path -Parent $OutputFile
if (-not (Test-Path -LiteralPath $folder -PathType Container)) {
    throw "Pasta de destino nao encontrada: $folder"
}

$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
    throw "Python launcher (py -3) nao encontrado. Instale Python 3, ou use o mesmo computador com Python usado na 0.4.4."
}

$secure = $null
$bstr = [IntPtr]::Zero
$keyPlain = $null
$hadPrevious = Test-Path Env:\RA_WEB_API_KEY
$previous = if ($hadPrevious) { $env:RA_WEB_API_KEY } else { $null }

try {
    if ($MetadataFile) {
        # Synthetic/local import option for independent CI and offline QA.
        $source = (Resolve-Path -LiteralPath $MetadataFile -ErrorAction Stop).ProviderPath
        Write-Host "Modo JSON local: sem consulta a API."
        & py -3 $scriptPath --game-extended $source --out $OutputFile
    }
    else {
        Write-Host ""
        Write-Host "DSi RA Bridge 0.4.5 - Catalogo oficial do Super Mario 64 DS" -ForegroundColor Cyan
        Write-Host "Jogo RA #9983 | Sem login no DSi | Sem awards | Sem modificacoes no SD"
        Write-Host ""
        Write-Host "Abra https://retroachievements.org/controlpanel.php"
        Write-Host "Em Keys, copie sua Web API Key."
        Write-Host "Cole a chave APENAS no prompt oculto abaixo. Nao envie ao chat nem ao GitHub." -ForegroundColor Yellow
        Write-Host ""
        $secure = Read-Host "Web API Key (entrada oculta)" -AsSecureString
        if ($null -eq $secure -or $secure.Length -lt 8) {
            throw "Chave vazia ou curta demais. Nenhuma consulta executada."
        }
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        $keyPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        if ([string]::IsNullOrWhiteSpace($keyPlain)) {
            throw "Chave vazia. Nenhuma consulta executada."
        }
        $env:RA_WEB_API_KEY = $keyPlain
        $keyPlain = $null
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        $bstr = [IntPtr]::Zero

        Write-Host "Consultando somente a API oficial, jogo 9983..."
        & py -3 $scriptPath --fetch-ra-api --out $OutputFile
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Importacao nao foi concluida (codigo $LASTEXITCODE). Revise o erro sem divulgar a chave."
    }
    if (-not (Test-Path -LiteralPath $OutputFile -PathType Leaf)) {
        throw "Importador encerrou sem criar relatorio."
    }
    $result = Get-Content -LiteralPath $OutputFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($result.game_id -ne 9983 -or $result.catalog_achievement_count -lt 1) {
        throw "Relatorio inconsistente com o jogo 9983. Nao utilize."
    }
    if ($result.gates.official_awards_sent -ne $false) {
        throw "Falha de seguranca: o relatorio deveria ter official_awards_sent=false."
    }
    Write-Host ""
    Write-Host "CATALOGO_045_IMPORTADO_COM_SUCESSO" -ForegroundColor Green
    Write-Host ("Conquistas indexadas: {0}" -f $result.catalog_achievement_count)
    Write-Host ("Catalogo SHA256: {0}" -f $result.catalog_revision_sha256)
    Write-Host ("Condicoes reais: {0}" -f $result.status)
    Write-Host ("Arquivo gerado: {0}" -f $OutputFile)
    Write-Host "Este JSON de cobertura nao contem a Web API Key. Pode ser analisado separadamente."
    Write-Host "Nao foi gerado pacote para o DSi. A 0.4.4 continua preservada."
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    $keyPlain = $null
    if ($null -ne $secure) { $secure.Dispose() }
    if ($hadPrevious) {
        $env:RA_WEB_API_KEY = $previous
    } else {
        Remove-Item Env:\RA_WEB_API_KEY -ErrorAction SilentlyContinue
    }
}
