@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT_DIR=%%~fI"

pushd "%ROOT_DIR%"

echo === AI Assistant source setup ===

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
echo echo Starting AI Assistant...
echo start venv\Scripts\pythonw.exe main.py
) > start_ai_assistant.bat

echo.
echo Setup completed.
echo You can now use start_ai_assistant.bat to launch the app locally.
pause

popd
endlocal
