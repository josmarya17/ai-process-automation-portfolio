@echo off
title Servidor Backend - Xara IA
echo ====================================================
echo         INICIANDO SERVIDOR BACKEND XARA IA          
echo ====================================================
echo.

cd /d "%~dp0\backend"

echo [1/2] Verificando e instalando dependencias si es necesario...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] No se pudieron instalar las dependencias. Asegurate de tener Python instalado y agregado al PATH.
    pause
    exit /b
)

echo [2/2] Iniciando aplicacion Uvicorn...
echo Servidor ejecutandose en http://localhost:8000
echo Presiona Ctrl+C en esta ventana para detener el servidor.
echo.

python app.py

if %errorlevel% neq 0 (
    echo [ERROR] El servidor se detuvo con un error.
    pause
)
