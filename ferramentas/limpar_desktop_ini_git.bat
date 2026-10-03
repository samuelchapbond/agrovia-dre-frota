@echo off
rem Apaga os desktop.ini que o Google Drive cria dentro de .git.
rem O git trata .git\refs\...\desktop.ini como uma referencia e o fetch/pull/push falham com
rem "bad object refs/desktop.ini". Funciona em qualquer maquina: o caminho vem da pasta deste ficheiro.
rem Uso manual: ferramentas\limpar_desktop_ini_git.bat (antes de git fetch/pull/push no terminal).
rem atualizar.bat e atualizar_local.bat chamam-no sozinhos.
setlocal
set "PASTA_GIT=%~dp0..\.git"
if not exist "%PASTA_GIT%\" exit /b 0

set /a APAGADOS=0
for /f "delims=" %%F in ('dir /s /b /a:-d "%PASTA_GIT%\desktop.ini" 2^>nul') do (
    del /f /q /a "%%F" >nul 2>&1
    if not exist "%%F" set /a APAGADOS+=1
)
for /f %%N in ('dir /s /b /a:-d "%PASTA_GIT%\desktop.ini" 2^>nul ^| find /c /v ""') do set "RESTANTES=%%N"
if %RESTANTES% gtr 0 echo [!] %RESTANTES% desktop.ini dentro de .git nao puderam ser apagados. Se o git falhar com "bad object", apague-os a mao.
if %APAGADOS% gtr 0 echo [git] %APAGADOS% desktop.ini do Google Drive apagado(s) de dentro de .git.

rem Ficheiros duplicados pelo Drive quando duas maquinas mexem no .git ao mesmo tempo (ex.: "index (1)").
dir /s /b /a:-d "%PASTA_GIT%\* (1)*" >nul 2>&1 && (
    echo [!] O Google Drive criou copias em conflito dentro de .git ^(nomes com " (1)"^).
    echo     Nao use o git noutra maquina ao mesmo tempo. Avise o responsavel antes de continuar.
)
exit /b 0
