@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================================================
echo   AGROVIA - QUARENTENA DE LANCAMENTOS
echo   Coloque o Excel exportado do Sankhya em dados\entrada_quarentena\
echo ====================================================================
echo.

python src\validar_entrada.py %*

if errorlevel 2 (
    echo.
    echo ====================================================================
    echo [!] Ha ficheiros RETIDOS com erro bloqueante.
    echo     Corrija os lancamentos no Sankhya, exporte de novo e substitua
    echo     o ficheiro em dados\entrada_quarentena\. Depois corra este .bat outra vez.
    echo ====================================================================
    start "" "saidas\relatorios_auditoria\pendencias_lancamentos.html"
    start "" "saidas\relatorios_auditoria\pendencias_lancamentos.xlsx"
    pause
    exit /b 2
)

if errorlevel 1 (
    echo.
    echo [X] ERRO: o validador falhou. Veja a mensagem acima.
    pause
    exit /b 1
)

echo.
echo [OK] Validacao concluida. Ficheiros sem bloqueantes ja estao em dados\banco_de_dados\.
if exist "saidas\relatorios_auditoria\pendencias_lancamentos.html" start "" "saidas\relatorios_auditoria\pendencias_lancamentos.html"
timeout /t 3 >nul
