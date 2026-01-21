@echo off
echo --- Configurazione Ambiente ai_assistant ---

:: 1. Crea l'ambiente virtuale se non esiste
if not exist venv (
    echo Creazione ambiente virtuale venv...
    python -m venv venv
)

:: 2. Aggiorna pip e installa le dipendenze
echo Installazione dipendenze in corso...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

:: 3. Crea il file di avvio (start_ai_assistant.bat)
echo Creazione file di avvio rapido...
(
echo @echo off
echo echo Avvio ai_assistant...
echo start venv\Scripts\pythonw.exe main.py
) > start_ai_assistant.bat

echo.
echo --- CONFIGURAZIONE COMPLETATA ---
echo Ora puoi usare 'start_ai_assistant.bat' per lanciare il programma.
pause