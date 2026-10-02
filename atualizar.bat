@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================================================
echo   AGROVIA - MOTOR DE GESTAO DE CUSTO DE FROTA (v8.32 Cloud Auto)
echo ====================================================================
echo.
echo [1/3] A executar o motor Python e a processar os dados do Sankhya...
python atualizar_dashboard.py

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [X] ERRO CRITICO: Falha no processamento Python.
    echo O processo foi abortado para proteger a integridade dos dados.
    echo ====================================================================
    echo.
    pause
    exit /b
)

echo.
echo [2/3] A sincronizar e a enviar a nova versao para a nuvem (GitHub)...
git add index.html
git commit -m "Auto-update DRE Agrovia: %date% %time%"
git push origin main

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [!] AVISO: O painel local foi atualizado, mas houve uma falha no Git Push.
    echo Verifique a sua ligacao a internet.
    echo ====================================================================
    echo.
    pause
    exit /b
)

echo.
echo ====================================================================
echo [3/3] Sincronizacao concluida com exito! A abrir o painel local...
echo ====================================================================
echo.

start index.html
timeout /t 3 >nul



