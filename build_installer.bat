@echo off
setlocal

echo === AI Assistant v3.3 installer build ===

if not exist venv\Scripts\python.exe (
    echo [ERRORE] Ambiente virtuale non trovato.
    exit /b 1
)

echo [1/2] Build onedir con PyInstaller...
venv\Scripts\python.exe -m PyInstaller --noconfirm --clean AI_Assistant_v3.3_onedir.spec
if errorlevel 1 (
    echo [ERRORE] Build PyInstaller fallita.
    exit /b 1
)

echo [2/2] Compilazione installer Inno Setup...
where iscc >nul 2>nul
if errorlevel 1 (
    echo [ATTENZIONE] Inno Setup non trovato.
    echo Installa Inno Setup e poi esegui:
    echo     iscc installer.iss
    exit /b 0
)

iscc installer.iss
if errorlevel 1 (
    echo [ERRORE] Compilazione installer fallita.
    exit /b 1
)

echo.
echo Build completata.
echo Installer disponibile in installer_output\AI_Assistant_Setup_v3.3.exe
endlocal
