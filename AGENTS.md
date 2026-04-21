# AGENTS.md

Note operative per Codex e per qualunque agente che lavori su questo progetto.

## Progetto

AI Assistant e una app desktop Windows tray-first per usare modelli AI locali.

La tray e il centro dell'app:

- scelta backend
- scelta modello
- analisi area/screenshot
- analisi testo copiato
- apertura chat
- configurazione
- about

La finestra chat e il workspace dove continuare, rileggere, cercare, rinominare, eliminare ed esportare le conversazioni.

## Percorso attuale

Workspace attuale:

```text
C:\Users\giuli\Documents\GitHub\AI_Assistant
```

Il vecchio workspace:

```text
E:\AI_Assistant.claude
```

potrebbe non esistere piu. Non usarlo come riferimento operativo.

## Comandi utili

Setup da sorgente:

```powershell
setup.bat
```

Avvio dopo il setup:

```powershell
start_ai_assistant.bat
```

Avvio diretto se l'ambiente e gia pronto:

```powershell
python main.py
```

Verifica sintassi principale:

```powershell
python -m py_compile main.py core\i18n.py
```

Verifica export:

```powershell
python -m py_compile main.py core\i18n.py services\export_service.py
```

Build installer:

```powershell
cmd /c setup\build_installer.bat
```

Output installer:

```text
installer_output\AI_Assistant_Setup_v3.4.exe
```

Aggiornamento asset release GitHub:

```powershell
gh release upload v3.4 installer_output\AI_Assistant_Setup_v3.4.exe --repo zoott28354/ai_assistant --clobber
```

## File locali da non committare

Non committare mai:

- `config.json`
- `chat_history.db`
- `venv/`
- `build/`
- `dist/`
- `installer_output/`
- `start_ai_assistant.bat`
- `__pycache__/`
- `.tmp/`

`config.json` contiene impostazioni runtime personali, come backend, modello attivo, lingua e prompt personalizzati.

`chat_history.db` contiene la cronologia reale delle chat, incluse eventuali immagini salvate come dati associati ai messaggi.

## File importanti del progetto

- `main.py`: finestra chat webview, bridge JS/Python e orchestrazione principale.
- `controllers/tray_controller.py`: controller tray-first, azioni tray e flusso screenshot/testo copiato.
- `core/app_meta.py`: metadati app, versione, publisher, URL.
- `core/config.py`: percorsi dati, config runtime, default.
- `core/i18n.py`: traduzioni UI e prompt default.
- `core/backends.py`: test backend e refresh modelli.
- `services/session_service.py`: SQLite, sessioni, salvataggio, rename/delete.
- `services/capture_service.py`: capture/snipping e immagini.
- `services/clipboard_service.py`: testo e clipboard.
- `services/export_service.py`: export chat ZIP/PDF.
- `services/tray_service.py`: costruzione menu tray.
- `ui/config_dialog.py`: finestra Configure.
- `ui/about_dialog.py`: finestra About.
- `workers/ai_worker.py`: chiamate backend AI.
- `setup/installer.iss`: script Inno Setup.
- `setup/AI_Assistant_onedir.spec`: spec PyInstaller generico.
- `setup/build_installer.bat`: build installer.
- `setup/generate_build_meta.py`: genera metadati build.

## Stato Git e release

Branch principale:

```text
main
```

Remote:

```text
origin https://github.com/zoott28354/ai_assistant.git
```

Prima di lavorare controllare sempre:

```powershell
git status -sb
```

La release pubblica attuale e:

```text
v3.4
```

Quando si cambia codice che finisce nell'installer:

1. commit e push su `main`
2. build installer con `setup\build_installer.bat`
3. upload asset release `v3.4` con `gh release upload ... --clobber`

## Note architetturali

Il progetto nasce da un refactor conservativo della vecchia app monolitica.

Non cambiare il comportamento tray-first senza esplicita richiesta.

Principio corretto:

- tray = controller operativo principale
- chat = workspace e storico persistente
- servizi = logica riusabile
- UI = input/visualizzazione

## Dati persistenti dell'app

Installazione normale:

```text
%AppData%\AI Assistant
```

Modalita portable:

```text
accanto all'eseguibile installato
```

Da sorgente:

```text
cartella progetto
```

File principali:

- `config.json`: backend, lingua, prompt personalizzati.
- `chat_history.db`: cronologia SQLite, incluse sessioni con immagini.

## Multilingua

La UI supporta:

- italiano
- inglese
- spagnolo
- francese
- tedesco
- portoghese
- russo
- giapponese
- cinese semplificato

Le stringhe UI vanno aggiunte in:

```text
core\i18n.py
```

L'installer e multilingua tramite Inno Setup.

Lingue installer incluse:

- italiano
- inglese
- spagnolo
- francese
- tedesco
- portoghese
- russo
- giapponese
- cinese semplificato

Il cinese richiede `ChineseSimplified.isl` installato nella cartella `Languages` di Inno Setup.

## Export ZIP/PDF

L'export chat e in lavorazione locale se non risulta ancora committato.

Obiettivo:

- menu `...` su ogni chat
- `Esporta ZIP`
- `Esporta PDF`

ZIP:

- deve contenere una cartella unica
- dentro: `.md`, `assets/`, `README_IMPORT.txt`
- il file `.md` deve avere nome chat + data chat
- le immagini devono stare in `assets/`
- per Obsidian bisogna estrarre tutta la cartella dentro il vault, non importare solo il `.md`

PDF:

- deve contenere testo, immagini, ruoli e metadati
- immagini ridimensionate, non in dimensione originale enorme
- stile pulito, non necessariamente identico pixel-perfect alla chat

File coinvolto:

```text
services\export_service.py
```

## Regole pratiche

- Non usare `git reset --hard` o comandi distruttivi senza richiesta esplicita.
- Non committare dati locali.
- Non modificare release/tag senza conferma.
- Dopo modifiche Python, eseguire almeno `py_compile`.
- Dopo modifiche installer, rigenerare setup e verificare che Inno Setup compili.
- Se si aggiorna il setup di una release, ricaricare l'asset GitHub con `--clobber`.
