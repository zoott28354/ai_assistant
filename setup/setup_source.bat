@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT_DIR=%%~fI"

pushd "%ROOT_DIR%"

echo === Sirius AI Tray Assistant source setup ===

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

echo Creating local launcher...
(
echo @echo off
echo echo Starting Sirius AI Tray Assistant...
echo start venv\Scripts\pythonw.exe main.py
) > start_sirius_ai_tray_assistant.bat

echo.
echo Setup completed.
echo You can now use start_sirius_ai_tray_assistant.bat to launch the app locally.
pause

popd
endlocal
