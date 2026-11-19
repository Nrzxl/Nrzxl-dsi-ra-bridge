# 034D gated diagnostic SD staging for PowerShell 5.1. Copies into NEW isolated directories only.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SdRoot,
    [Parameter(Mandatory = $true)][string]$RomPath,
    [Parameter(Mandatory = $true)][switch]$BackupConfirmed
)
$ErrorActionPreference = 'Stop'
if (-not $BackupConfirmed) { throw "Make a full backup and pass -BackupConfirmed." }
$root = (Resolve-Path -LiteralPath $SdRoot).ProviderPath.TrimEnd('\')
if ($root -notmatch '^[A-Za-z]:$') { throw "Pass an SD drive root such as D:\." }
$root += '\'
if (-not (Test-Path -LiteralPath (Join-Path $root 'boot.nds') -PathType Leaf)) {
    throw "boot.nds missing. Check the drive!"
}
if (-not (Test-Path -LiteralPath (Join-Path $root 'private'))) {
    throw "private folder missing. Check the drive!"
}
$game = (Resolve-Path -LiteralPath $RomPath).ProviderPath
if ([IO.Path]::GetExtension($game) -ine '.nds') { throw "Only .nds files." }
$size = (Get-Item -LiteralPath $game).Length
if ($size -lt 512 -or $size -gt 67108864) { throw "Unexpected .nds file size." }
$packageRoot = $PSScriptRoot
$statusPath = Join-Path $packageRoot 'STATUS.json'
if (-not (Test-Path -LiteralPath $statusPath)) { throw "Extract inner ZIP first." }
$manifest = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
if ($manifest.version -ne '0.3.4-D-offline-only' -or
    $manifest.offline_by_default -ne $true -or
    $manifest.no_game_in_package -ne $true -or
    $manifest.retroachievements -ne 'DISABLED') {
    throw "Package not approved for the offline-only test."
}
$folders = @('nds\DSiRABridge_034D', '_nds\dsirb034d',
             '_nds\dsirb034d-cache', 'DSiRABridge_034D')
foreach ($rel in $folders) {
    if (Test-Path -LiteralPath (Join-Path $root $rel)) {
        throw "New test folder already exists: $rel. Refusing overwrite."
    }
}
$required = @(
    'nds\DSiRABridge_034D\DSIRB_Launcher_034D.nds',
    '_nds\dsirb034d\nds-bootstrap.nds',
    '_nds\dsirb034d\dscheevos9.bin',
    '_nds\dsirb034d\load.bin'
)
foreach ($rel in $required) {
    $src = Join-Path $packageRoot $rel
    if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "Missing: $rel" }
    $hashName = $rel.Replace('\', '/')
    $expected = [string]($manifest.checksums.PSObject.Properties[$hashName].Value)
    $actual = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant()
    if (-not $expected -or $actual -ne $expected.ToLowerInvariant()) {
        throw "Hash mismatch: $rel"
    }
}
$ini = Get-Content -LiteralPath (Join-Path $packageRoot '_nds\dsirb034d\dscheevos.ini') -Raw
if ($ini -notmatch '(?m)^ENABLED = 0\s*$' -or
    $ini -notmatch '(?m)^SPECTATOR = 1\s*$' -or
    $ini -notmatch '(?m)^TOKEN =\s*$') {
    throw "Offline mode not enforced."
}
$stable = @('boot.nds', '_nds\nds-bootstrap-release.nds',
            '_nds\nds-bootstrap-nightly.nds', '_nds\nds-bootstrap.ini')
$before = @{}
foreach ($rel in $stable) {
    $p = Join-Path $root $rel
    if (Test-Path -LiteralPath $p -PathType Leaf) {
        $before[$rel] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
    }
}
Write-Host "Offline only. Does not install RA on your stable bootstrap." -ForegroundColor Yellow
Write-Host "SD: $root"
Write-Host "ROM: $game"
if ((Read-Host "Type STAGE to copy to the experimental SD directories") -cne 'STAGE') {
    throw "Cancelled; no files written."
}
try {
    Copy-Item -LiteralPath (Join-Path $packageRoot 'nds\DSiRABridge_034D') -Destination (Join-Path $root 'nds\DSiRABridge_034D') -Recurse -ErrorAction Stop
    Copy-Item -LiteralPath (Join-Path $packageRoot '_nds\dsirb034d') -Destination (Join-Path $root '_nds\dsirb034d') -Recurse -ErrorAction Stop
    New-Item -ItemType Directory -Path (Join-Path $root '_nds\dsirb034d-cache') -ErrorAction Stop | Out-Null
    $test = Join-Path $root 'DSiRABridge_034D'
    New-Item -ItemType Directory -Path (Join-Path $test 'games') -Force -ErrorAction Stop | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $test 'saves') -Force -ErrorAction Stop | Out-Null
    Copy-Item -LiteralPath $game -Destination (Join-Path $test 'games\selected.nds') -ErrorAction Stop
    if ((Get-FileHash -LiteralPath (Join-Path $test 'games\selected.nds') -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $game -Algorithm SHA256).Hash) {
        throw "Copied ROM differs from source."
    }
    foreach ($rel in $stable) {
        $p = Join-Path $root $rel
        if ($before.ContainsKey($rel) -and
            (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $before[$rel]) {
            throw "Stable file changed: $rel"
        }
    }
    Write-Host "STAGED. Hardware boot still NOT_RUN." -ForegroundColor Green
    Write-Host "Eject SD. Flipnote Lenny > HBMenu > nds/DSiRABridge_034D/DSIRB_Launcher_034D.nds"\n    Write-Host "STOP at S4 gate and report early stages before attempting chainload."
    Write-Host "If you see an RA login prompt or errors, STOP."
} catch {
    Write-Warning "Stage incomplete. Do not boot. Remove ONLY the new 034D directories after checking."
    throw
}
