@echo off
setlocal

echo === AI Assistant v3.4 installer build ===

if not exist venv\Scripts\python.exe (
    echo [ERRORE] Ambiente virtuale non trovato.
    exit /b 1
)

echo [1/2] Build onedir con PyInstaller...
venv\Scripts\python.exe -m PyInstaller --noconfirm --clean AI_Assistant_v3.4_onedir.spec
if errorlevel 1 (
    echo [ERRORE] Build PyInstaller fallita.
    exit /b 1
)

echo [2/2] Compilazione installer Inno Setup...
set "ISCC_EXE="
where iscc >nul 2>nul
if not errorlevel 1 set "ISCC_EXE=iscc"
if not defined ISCC_EXE if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE (
    echo [ATTENZIONE] Inno Setup non trovato.
    echo Installa Inno Setup e poi esegui:
    echo     "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    exit /b 0
)

"%ISCC_EXE%" installer.iss
if errorlevel 1 (
    echo [ERRORE] Compilazione installer fallita.
    exit /b 1
)

echo.
echo Build completata.
echo Installer disponibile in installer_output\AI_Assistant_Setup_v3.4.exe
endlocal
