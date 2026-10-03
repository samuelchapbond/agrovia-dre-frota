@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================================================
echo   AGROVIA - MOTOR DE GESTAO DE CUSTO DE FROTA (v8.32 Cloud Auto)
echo ====================================================================
echo.
if exist "dados\entrada_quarentena\*.xls*" (
    echo [0/4] Ficheiros em dados\entrada_quarentena: a validar antes de entrarem em dados\banco_de_dados...
    python src\validar_entrada.py
    echo     Pendencias em: saidas\relatorios_auditoria\pendencias_lancamentos.xlsx / .html
    echo     Ficheiros retidos nao entram no painel desta execucao.
    echo.
)

echo [1/4] A executar o motor Python e a processar os dados do Sankhya...
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
echo [2/4] A executar o auditor antes de publicar...
python src\auditoria_completa.py

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [X] PUBLICACAO BLOQUEADA: a auditoria falhou.
    echo     Nada foi enviado para o GitHub.
    echo Motivos em: saidas\relatorios_auditoria\veredito_publicacao.txt
    echo O index.html local NAO esta auditado e nao deve ser commitado a mao.
    echo ====================================================================
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] A sincronizar e a enviar a nova versao para a nuvem (GitHub)...
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
    exit /b 1
)

echo.
echo ====================================================================
echo [4/4] Sincronizacao concluida com exito! A abrir o painel local...
echo ====================================================================
echo.

start index.html
timeout /t 3 >nul



