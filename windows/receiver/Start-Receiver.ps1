#Requires -Version 5.1
[CmdletBinding()]
param([switch]$Lan,[int]$Port=18216,[int]$WebPort=18217)
$ErrorActionPreference='Stop'
Get-Command node -ErrorAction Stop | Out-Null
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$bind='127.0.0.1'
if($Lan){$bind='0.0.0.0'}
$argsNode=@((Join-Path $PSScriptRoot 'server.cjs'),'--bind',$bind,'--port',"$Port",'--web',"$WebPort",'--logDir',(Join-Path $root 'logs-030'))
$engine=Join-Path $root 'bin\dsirb_live.exe'
if(Test-Path -LiteralPath $engine){$argsNode+=@('--engine',$engine)}
Write-Host "Receiver: http://127.0.0.1:$WebPort"
Write-Host "UDP: $bind port $Port. No firewall changes are made."
& node @argsNode
