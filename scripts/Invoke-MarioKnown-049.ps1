<# DSi RA Bridge 049: Windows PowerShell 5.1 read-only ASMP PC lab. #>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('coin_up','star_up','life_down','health_down','level_change','idle_no_event')]
  [string]$Event,
  [string]$BasePrefix,
  [string]$OutputPath,
  [string]$RomPath,
  [switch]$AllowUnverifiedHeader,
  [int]$CoinsBefore = -1,
  [int]$CoinsAfter = -1
)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'
$analyzer = Join-Path $PSScriptRoot 'inspect-asmp-known-049.py'
if (-not (Test-Path -LiteralPath $analyzer -PathType Leaf)) {
  throw '049 analyzer not found; extract entire PC package.'
}
$downloads = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads'
if (-not $BasePrefix) {
  $latest = @(Get-ChildItem -LiteralPath $downloads -Filter 'DSi048_ASMP_*_after.bin' -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1)
  if ($latest.Count -ne 1) { throw 'No AFTER capture in Downloads.' }
  $BasePrefix = $latest[0].FullName.Substring(0,$latest[0].FullName.Length - '_after.bin'.Length)
}
$base = [IO.Path]::GetFullPath($BasePrefix)
foreach ($suffix in @('_before.bin','_idle.bin','_after.bin')) {
  if (-not (Test-Path -LiteralPath ($base+$suffix) -PathType Leaf)) {
    throw "Incomplete 048 set: $base$suffix"
  }
}
if (-not $OutputPath) {
  $name = [IO.Path]::GetFileName($base)
  $OutputPath = Join-Path $downloads ("DSi049_" + $Event + "_" + $name + ".json")
}
if (Test-Path -LiteralPath $OutputPath) {
  throw "Already analyzed this capture/event: $OutputPath"
}
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python launcher py -3 not found.' }
$args049 = @('-3',$analyzer,'--before',($base+'_before.bin'),
  '--idle',($base+'_idle.bin'),'--after',($base+'_after.bin'),
  '--event',$Event,'--out',$OutputPath)
if ($RomPath) {
  $rom = (Resolve-Path -LiteralPath $RomPath -ErrorAction Stop).ProviderPath
  $args049 += @('--rom',$rom)
} elseif ($AllowUnverifiedHeader) {
  $args049 += '--allow-unverified-header'
}
if ($CoinsBefore -ge 0 -or $CoinsAfter -ge 0) {
  if ($CoinsBefore -lt 0 -or $CoinsAfter -lt 0) { throw 'Provide both coin values.' }
  $args049 += @('--expected-coins-before',[string]$CoinsBefore,
    '--expected-coins-after',[string]$CoinsAfter)
}
Write-Host ("049 ASMP PC READ ONLY: {0}" -f $base)
& py @args049
if ($LASTEXITCODE -ne 0) { throw '049 analysis blocked; read previous message.' }
Write-Host ("RELATORIO_049: {0}" -f $OutputPath) -ForegroundColor Green
Write-Host 'Upload only sanitized JSON; ROM and BIN remain private.'
