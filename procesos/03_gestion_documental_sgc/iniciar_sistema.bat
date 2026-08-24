@echo off
title Enterprise SGC BPM Automator - Iniciar Sistema
color 0B

echo =================================================================
echo             Enterprise SGC BPM AUTOMATOR - INICIAR SISTEMA
echo =================================================================
echo.
cd /d "C:\Users\Sist-JPinto\Desktop\Sistema de Gestion Documental"

echo [1/2] Iniciando el servidor local de Streamlit en el puerto 8510...
echo [2/2] Abriendo el panel interactivo en http://localhost:8510 en tu navegador...
echo.
echo Presiona Ctrl+C en esta ventana de terminal si deseas detener el sistema.
echo -----------------------------------------------------------------
echo.

python -m streamlit run app.py --server.port 8510

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Ocurrio un fallo al intentar iniciar Streamlit.
    echo Asegurate de tener Python y las dependencias de requirements.txt instaladas.
    echo.
    pause
)
