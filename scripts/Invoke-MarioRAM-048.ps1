<#
.SYNOPSIS
  DSi RA Bridge 0.4.8 - analisar o ultimo conjunto privado de RAM BizHawk.
.DESCRIPTION
  Funciona em Windows PowerShell 5.1. Nao instala nem executa ROM, apenas
  compara 3 capturas privadas ja criadas no PC pelo Lua no BizHawk.
  Nao envia dados ao RA nem altera a ROM, DSi ou cartao SD.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-MarioRAM-048.ps1 -Event coin_up -RomPath 'E:\Mario ASMP Europa.nds'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('coin_up', 'star_up', 'life_down', 'health_down', 'level_change')]
    [string]$Event,
    [string]$RomPath,
    [switch]$AllowUnverifiedHeader,
    [string]$BasePrefix,
    [string]$OutputPath
)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'
$analyzer = Join-Path $PSScriptRoot 'analyze-asmp-ram-048.py'
if (-not (Test-Path -LiteralPath $analyzer -PathType Leaf)) {
    throw 'Analizador ausente. Use o ZIP da 0.4.8 completo.'
}
if (-not $BasePrefix) {
    $downloads = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads'
    $last = @(Get-ChildItem -LiteralPath $downloads -Filter 'DSi048_ASMP_*_before.bin' -File |
      Sort-Object LastWriteTime -Descending | Select-Object -First 1)
    if ($last.Count -ne 1) {
        throw 'Nenhuma captura BEFORE encontrada em Downloads. Execute o Lua no BizHawk primeiro.'
    }
    $BasePrefix = $last[0].FullName.Substring(0, $last[0].FullName.Length - '_before.bin'.Length)
}
$base = [IO.Path]::GetFullPath($BasePrefix)
$before = $base + '_before.bin'
$idle = $base + '_idle.bin'
$after = $base + '_after.bin'
foreach ($p in @($before,$idle,$after)) {
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
        throw "Captura incompleta. Arquivo nao encontrado: $p"
    }
}
if (-not $OutputPath) {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $OutputPath = Join-Path ([Environment]::GetFolderPath('UserProfile')) ("Downloads\DSi048_" + $Event + "_candidatos_" + $stamp + ".json")
}
if (Test-Path -LiteralPath $OutputPath) {
    throw "Nao sobrescrevo relatorios anteriores: $OutputPath"
}
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw 'Python 3 nao encontrado (comando py -3).'
}
$invoke = @(
    '-3', $analyzer,
    '--before', $before,
    '--idle', $idle,
    '--after', $after,
    '--event', $Event,
    '--out', $OutputPath
)
if ($RomPath) {
    $rom = (Resolve-Path -LiteralPath $RomPath -ErrorAction Stop).ProviderPath
    $invoke += @('--rom', $rom)
} elseif ($AllowUnverifiedHeader) {
    Write-Warning 'Sem ROM homologada local; report marcara identidade nao confirmada.'
    $invoke += '--allow-unverified-header'
}
Write-Host 'DSi RA Bridge 0.4.8 — diagnostico somente leitura no PC'
Write-Host ('Evento observado: {0}' -f $Event)
Write-Host ('Capturas: {0}' -f $base)
& py @invoke
if ($LASTEXITCODE -ne 0) {
    throw 'Analisador bloqueou a execucao; leia a mensagem anterior. Nenhum arquivo foi alterado.'
}
Write-Host ('RELATORIO_SANITIZADO: {0}' -f $OutputPath) -ForegroundColor Green
Write-Host 'Envie apenas o JSON final; nunca envie os tres arquivos BIN, ROM ou save.'
