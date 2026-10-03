@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================================================
echo   AGROVIA - MOTOR DE GESTAO DE CUSTO DE FROTA (Atualizacao LOCAL)
echo   Nada e enviado para o GitHub. Para publicar use atualizar.bat
echo ====================================================================
echo.
call ferramentas\limpar_desktop_ini_git.bat
echo [1/3] A executar o motor Python e a processar os dados do Sankhya...
python src\atualizar_dashboard.py

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [X] ERRO CRITICO: Falha no processamento Python.
    echo O processo foi abortado para proteger a integridade dos dados.
    echo ====================================================================
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] A executar o auditor...
python src\auditoria_completa.py

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [!] AUDITORIA REPROVADA: o painel local foi gerado, mas NAO esta
    echo     apto a ser publicado.
    echo Motivos em: saidas\relatorios_auditoria\veredito_publicacao.txt
    echo ====================================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo [3/3] Painel local atualizado e auditado. A abrir o painel...
echo ====================================================================
echo.

start index.html
timeout /t 3 >nul
