@echo off
setlocal
where node >nul 2>nul
if errorlevel 1 (
 echo Node.js nao encontrado. Instale uma versao LTS oficial e abra novamente.
 pause
 exit /b 1
)
set "BIND=127.0.0.1"
if /I "%~1"=="--lan" set "BIND=0.0.0.0"
echo Receiver 0.3.2: http://127.0.0.1:18217
echo UDP %BIND%:18216. Nenhuma politica PowerShell e alterada.
if exist "%~dp0..\..\bin\dsirb_live.exe" (
 node "%~dp0server.cjs" --bind %BIND% --logDir "%~dp0..\..\logs-032" --engine "%~dp0..\..\bin\dsirb_live.exe"
) else (
 node "%~dp0server.cjs" --bind %BIND% --logDir "%~dp0..\..\logs-032"
)
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" pause
exit /b %RESULT%
