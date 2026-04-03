@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT_DIR=%%~fI"

pushd "%ROOT_DIR%"

echo === AI Assistant installer build ===

if not exist venv\Scripts\python.exe (
    echo [ERROR] Virtual environment not found.
    popd
    exit /b 1
)

echo [1/3] Generating build metadata...
venv\Scripts\python.exe setup\generate_build_meta.py
if errorlevel 1 (
    echo [ERROR] Metadata generation failed.
    popd
    exit /b 1
)

echo [2/3] Building onedir package with PyInstaller...
venv\Scripts\python.exe -m PyInstaller --noconfirm --clean setup\AI_Assistant_onedir.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    popd
    exit /b 1
)

echo [3/3] Building Inno Setup installer...
set "ISCC_EXE="
where iscc >nul 2>nul
if not errorlevel 1 set "ISCC_EXE=iscc"
if not defined ISCC_EXE if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE (
    echo [WARNING] Inno Setup not found.
    echo Install Inno Setup and then run:
    echo     "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup\installer.iss
    popd
    exit /b 0
)

"%ISCC_EXE%" setup\installer.iss
if errorlevel 1 (
    echo [ERROR] Installer build failed.
    popd
    exit /b 1
)

echo.
echo Build completed.
echo Installer available in installer_output\
popd
endlocal
