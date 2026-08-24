@echo off
:: Script para ejecutar el procesador de extractos bancarios

:: Cambiar al directorio del script
cd /d "%~dp0"

echo ==================================================
echo   Procesador de Extractos Bancarios
echo ==================================================
echo.

:: Verificar si python esta en el PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_BIN=python
) else (
    :: Fallback a la ruta especifica detectada en su sistema
    if exist "C:\Users\Sist-JPinto\AppData\Local\Programs\Python\Python310\python.exe" (
        set PYTHON_BIN="C:\Users\Sist-JPinto\AppData\Local\Programs\Python\Python310\python.exe"
    ) else (
        echo ERROR: No se encontro Python instalado. 
        echo Por favor asegurese de tener Python agregado al PATH.
        goto end
    )
)

:: Ejecutar el script mostrando el resultado en pantalla en tiempo real
%PYTHON_BIN% -u process_statements.py

:end
echo.
echo ==================================================

:: Si se ejecuta desde el Programador de Tareas, pasar el parametro --scheduled
:: Ejemplo: run_process.bat --scheduled
:: Esto evitara que la consola se quede pausada esperando entrada de teclado.
if "%1"=="--scheduled" (
    echo Ejecucion automatizada completada.
) else (
    echo.
    echo Presione cualquier tecla para cerrar esta ventana...
    pause > nul
)
