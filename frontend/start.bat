@echo off
chcp 65001 >nul
title SkyCamOS - Frontend PWA

echo ============================================================
echo            SkyCamOS - Frontend PWA
echo ============================================================
echo.

REM Verifica se Node.js esta instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado. Instale o Node.js 18+
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/2] Instalando dependencias...
echo.
cd /d "%~dp0"
call npm install --silent
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas
echo.

echo [2/2] Iniciando servidor de desenvolvimento...
echo.
echo Frontend rodando em: http://localhost:3000
echo.
echo IMPORTANTE: O backend deve estar rodando em http://localhost:8000
echo.
echo Pressione CTRL+C para parar o servidor
echo ============================================================
echo.

call npm run dev

pause
