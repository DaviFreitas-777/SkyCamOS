@echo off
chcp 65001 >nul
title SkyCamOS - Inicializacao

echo ============================================================
echo            SkyCamOS - Sistema de Monitoramento
echo ============================================================
echo.

REM Verifica se Python esta instalado
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale o Python 3.10+
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias...
echo.
cd /d "%~dp0"
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas
echo.

echo [2/3] Verificando banco de dados...
echo.
cd /d "%~dp0"
if not exist "data" mkdir data
if not exist "data\skycamos.db" (
    echo Banco de dados sera criado automaticamente ao iniciar
) else (
    echo [OK] Banco de dados ja existe
)
echo.

echo [3/3] Iniciando servidor...
echo.
echo Servidor rodando em: http://127.0.0.1:8000
echo Documentacao API: http://127.0.0.1:8000/docs
echo.
echo Pressione CTRL+C para parar o servidor
echo ============================================================
echo.

cd /d "%~dp0"
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
