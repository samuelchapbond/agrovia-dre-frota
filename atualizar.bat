@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================================================
echo   AGROVIA - MOTOR DE GESTAO DE CUSTO DE FROTA (v8.32 Multi-Agent)
echo ====================================================================
echo.
echo [ETL] A varrer a pasta 'Banco_de_Dados' e a processar o Sankhya...
echo.

python atualizar_dashboard.py

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [X] ERRO CRITICO: Falha no processamento do motor Python.
    echo Verifique se ha ficheiros Excel abertos ou se a pasta esta vazia.
    echo ====================================================================
    echo.
    pause
    exit /b
)

echo.
echo ====================================================================
echo [SUCESSO] Processo concluido e auditado com exito pelos Agentes!
echo A abrir o painel atualizado no navegador...
echo ====================================================================
echo.

start index.html
timeout /t 3 >nul


