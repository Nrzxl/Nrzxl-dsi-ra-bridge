#Requires -Version 5.1
[CmdletBinding()]
param([string]$Image = 'devkitpro/devkitarm:20241104')
$ErrorActionPreference = 'Stop'
foreach ($tool in @('docker','node','python','git')) {
    Get-Command $tool -ErrorAction Stop | Out-Null
}
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $commit = (& git rev-parse --verify HEAD | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[a-f0-9]{40}$') {
        throw 'Initialize and commit this experimental repository first.'
    }
    $dirty = (& git status --porcelain --untracked-files=normal | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Commit source changes before building; source SHA must identify the inputs.' }
    $resolved = (& docker image inspect --format '{{index .RepoDigests 0}}' $Image | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $resolved -notmatch '^devkitpro/devkitarm@sha256:[a-f0-9]{64}$') {
        throw 'Install the documented official image first; this script does not install SDKs.'
    }
    $outputDir = Join-Path $projectRoot ('out\local-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
    New-Item -ItemType Directory -Path $outputDir | Out-Null
    foreach ($test in @('tests/protocol-tests.cjs','tests/client-tests.cjs','tests/nds-format-tests.cjs')) {
        & node $test
        if ($LASTEXITCODE -ne 0) { throw "Regression FAIL: $test" }
    }
    foreach ($pass in @('first','second')) {
        $argsDocker = @('run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,exec','--tmpfs','/work:rw,exec','--mount',"type=bind,source=$projectRoot,target=/src,readonly",'--mount',"type=bind,source=$outputDir,target=/out",'-w','/work',$resolved,'bash','/src/scripts/build-arm-020.sh',$pass)
        & docker @argsDocker 2>&1 | Tee-Object -FilePath (Join-Path $outputDir "build-$pass.log")
        if ($LASTEXITCODE -ne 0) { throw "ARM build FAIL: $pass. Preserve logs." }
        & node scripts/validate-nds.cjs (Join-Path $outputDir "$pass\DSiRABridge_Diagnostic_020.nds") (Join-Path $outputDir "$pass\structure.json")
        if ($LASTEXITCODE -ne 0) { throw "NDS structure FAIL: $pass" }
    }
    Set-Content -LiteralPath (Join-Path $outputDir 'image-digest.txt') -Value $resolved -Encoding ASCII
    Set-Content -LiteralPath (Join-Path $outputDir 'source-commit.txt') -Value $commit -Encoding ASCII
    & python scripts/package-sd-020.py --root $outputDir --commit $commit --image $resolved
    if ($LASTEXITCODE -ne 0) { throw 'Packaging or reproducibility FAIL' }
    Write-Output "Candidate SD ZIP: $outputDir"
    Write-Output 'Hardware NOT_RUN. Nothing copied to the SD.'
} finally {
    Pop-Location
}
