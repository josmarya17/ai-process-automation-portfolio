@echo off
cd /d "%~dp0"
echo =================================================== >> scratch\run_log.txt
echo [%DATE% %TIME%] Iniciando actualizacion diaria GA4 para WAC... >> scratch\run_log.txt
python scratch\update_ga4_sheet.py >> scratch\run_log.txt 2>&1
if %errorlevel% neq 0 (
    echo [%DATE% %TIME%] [ERROR] La actualizacion fallo con codigo %errorlevel%. >> scratch\run_log.txt
) else (
    echo [%DATE% %TIME%] [OK] La actualizacion finalizo correctamente. >> scratch\run_log.txt
)
echo =================================================== >> scratch\run_log.txt
