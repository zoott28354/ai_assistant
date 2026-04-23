# AGENTS.md

Note operative per Codex e per qualunque agente che lavori su questo progetto.

## Progetto

Sirius AI Tray Assistant e una app desktop Windows tray-first per usare modelli AI locali.

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
E:\AI_Assistant.claude
```

Nota: in alcuni momenti e stata usata anche questa copia:

```text
C:\Users\giuli\Documents\GitHub\AI_Assistant
```

Non cambiare workspace senza confermare con l'utente e senza controllare `git status -sb`.

## Comandi utili

Setup da sorgente:

```powershell
setup.bat
```

Avvio dopo il setup:

```powershell
start_sirius_ai_tray_assistant.bat
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
installer_output\Sirius_AI_Tray_Assistant_Setup_v3.6.0.exe
```

Aggiornamento asset release GitHub:

```powershell
gh release upload v3.6.0 installer_output\Sirius_AI_Tray_Assistant_Setup_v3.6.0.exe --repo zoott28354/sirius-ai-tray-assistant --clobber
```

## File locali da non committare

Non committare mai:

- `config.json`
- `chat_history.db`
- `venv/`
- `build/`
- `dist/`
- `installer_output/`
- `start_sirius_ai_tray_assistant.bat`
- `__pycache__/`
- `.vs/`
- `.tmp/`
- `*.log`

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
- `services/attachment_service.py`: lettura allegati chat, immagini, documenti testuali, DOCX, PDF e fallback OCR/vision tramite rendering pagine PDF.
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
origin https://github.com/zoott28354/sirius-ai-tray-assistant.git
```

Prima di lavorare controllare sempre:

```powershell
git status -sb
```

La release pubblica attuale e:

```text
v3.6.0
```

Quando si cambia codice che finisce nell'installer:

1. commit e push su `main`
2. build installer con `setup\build_installer.bat`
3. upload asset release `v3.6.0` con `gh release upload ... --clobber`

## Note architetturali

Il progetto nasce da un refactor conservativo della vecchia app monolitica.

Non cambiare il comportamento tray-first senza esplicita richiesta.

Principio corretto:

- tray = controller operativo principale
- chat = workspace e storico persistente
- servizi = logica riusabile
- UI = input/visualizzazione

## Dati persistenti dell'app

Installazione installer Windows:

```text
app per utente corrente oppure per tutti gli utenti
dati utente in %AppData%\Sirius AI Tray Assistant
```

L'installer usa la scelta Inno Setup `utente corrente / tutti gli utenti`: per tutti gli utenti l'app va in `C:\Program Files\Sirius AI Tray Assistant`, mentre per utente corrente usa il percorso app per-user di Windows.

I dati utente restano sempre separati per ogni account Windows in `%AppData%\Sirius AI Tray Assistant`.

L'installer non propone piu la modalita portable. La task opzionale `Avvia all'avvio di Windows` registra l'app in `HKCU` o `HKLM` tramite root Inno `HKA`, in base al tipo di installazione scelto.

Installazione portable legacy/manuale:

```text
accanto all'eseguibile installato
```

Da sorgente:

```text
cartella progetto
```

File principali:

- `config.json`: backend, lingua, prompt personalizzati.
- `chat_history.db`: cronologia SQLite, incluse sessioni con immagini, allegati originali e pagine PDF renderizzate per OCR/vision quando necessario.

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

## Allegati Chat

La chat supporta il pulsante `+` nel composer.

Allegati supportati:

- immagini: inviate come input multimodale al backend compatibile
- file di testo, Markdown, codice, CSV, JSON, YAML, log: letti e inseriti come contesto testuale
- DOCX: testo estratto dal documento
- PDF: testo estratto tramite `pypdf`; se non c'e testo estraibile, le pagine vengono renderizzate con `pymupdf` e inviate come immagini al modello OCR/vision compatibile

Gli allegati vengono salvati nella cronologia come parte del messaggio inviato:

- immagini nei campi immagine del messaggio
- documenti con testo estratto, nome file e binario originale in base64
- PDF scansionati con file originale e pagine renderizzate in memoria/base64 per il modello

In chat i documenti devono restare visibili come allegati/chip, non venire incollati nel testo visibile del messaggio. Il testo estratto viene aggiunto solo al prompt interno passato all'LLM.

## Backend Custom

`Custom 1` e `Custom 2` sono endpoint OpenAI-compatible generici.

Ogni custom puo avere:

- URL endpoint
- API key opzionale
- Nome visuale

Il nome visuale deve comparire nella tray, nel badge alto della chat e nella sidebar, mentre il backend interno resta `Custom 1` o `Custom 2`.

## Export ZIP/PDF

L'export chat e disponibile dal menu `...` di ogni chat.

Obiettivo:

- menu `...` su ogni chat
- `Esporta ZIP`
- `Esporta PDF`

ZIP:

- deve contenere una cartella unica
- dentro: `.md` e, se presenti immagini o documenti allegati, `assets/`
- il file `.md` deve avere nome chat + data chat
- immagini e documenti originali allegati devono stare in `assets/`
- per Obsidian bisogna estrarre tutta la cartella dentro il vault, non importare solo il `.md`

PDF:

- deve contenere testo, immagini, ruoli e metadati
- immagini ridimensionate, non in dimensione originale enorme
- stile pulito, non necessariamente identico pixel-perfect alla chat

File coinvolto:

```text
services\export_service.py
```

## Manutenzione Database

La finestra Configure include una tab `Manutenzione`.

Funzioni:

- `Apri cartella dati`: apre in Explorer la cartella che contiene `config.json` e `chat_history.db`
- `Compatta database`: elimina fisicamente le sessioni gia marcate come cancellate e poi esegue `VACUUM`

Nota importante: cancellare una chat dalla UI fa soft-delete. Lo spazio su disco viene recuperato solo quando si usa `Compatta database`.

## Regole pratiche

- Non usare `git reset --hard` o comandi distruttivi senza richiesta esplicita.
- Non committare dati locali.
- Non modificare release/tag senza conferma.
- Dopo modifiche Python, eseguire almeno `py_compile`.
- Dopo modifiche installer, rigenerare setup e verificare che Inno Setup compili.
- Se si aggiorna il setup di una release, ricaricare l'asset GitHub con `--clobber`.
