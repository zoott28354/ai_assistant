# 👁️ AI Assistant v3.4

Un assistente AI locale per Windows pensato per lavorare davvero bene dal desktop: cattura schermate, legge testo dagli appunti, invia immagini o prompt ai tuoi modelli locali e mantiene una cronologia persistente delle conversazioni.

L'idea del progetto è semplice: avere un assistente sempre pronto nella system tray per tradurre, spiegare, analizzare immagini, leggere errori a schermo e continuare il flusso in chat senza dipendere dal cloud.

## ✨ Perché usarlo

- 🔒 **Tutto resta locale**: screenshot, testo copiato e cronologia non vengono inviati a servizi esterni.
- 🤖 **Più backend supportati**: Ollama, LM Studio, Llama.cpp e Llama-Swap.
- ⚡ **Flusso rapido da desktop**: parti da una cattura schermo o da un testo copiato e continui subito in chat.
- 🧠 **Cronologia persistente**: le sessioni vengono salvate in SQLite e riprese in seguito.
- 🖥️ **UI aggiornata in v3.4**: chat più moderna in webview, sidebar migliorata, flussi più stabili e supporto multilingua dell'interfaccia.

## 🚀 Novità della v3.4

- 💬 Nuova chat desktop con rendering web-based integrato in PyQt.
- 📚 Sidebar cronologia più leggibile, ridimensionabile e con eliminazione singola delle chat.
- 🗂️ Persistenza sessioni corretta e ordinamento basato sull'ultima attività.
- 🖱️ Scroll e comportamento della chat migliorati.
- 📸 `Analizza Area` ora usa il ritaglio nativo di Windows.
- 🌈 Migliore compatibilità pratica con sistemi HDR grazie al passaggio al capture nativo.
- 🧩 Supporto esplicito a `PyQt6-WebEngine` per la nuova UI.
- 🌍 Interfaccia multilingua con supporto per italiano, inglese, spagnolo, francese, tedesco e portoghese.

## 🛠️ Funzioni principali

- 📸 **Analizza Area**  
  Apre il ritaglio nativo di Windows, acquisisce la selezione e la invia al modello.

- 📋 **Analizza Testo Copiato**  
  Prende il contenuto dagli appunti e lo manda subito in analisi.

- 💬 **Chat persistente**  
  Puoi continuare una conversazione esistente oppure aprirne una nuova.

- 🔌 **Multi-backend locale**  
  Scegli backend e modello dal menu nella tray.

- ⚙️ **Configurazione backend persistente**  
  Gli URL vengono salvati in `config.json`.

- 🖼️ **Supporto immagini**  
  Le richieste con immagini vengono gestite dai backend compatibili.

## 🤖 Backend supportati

L'app nasce per lavorare con backend locali compatibili con i modelli già installati sulla tua macchina.

- Ollama
- LM Studio
- Llama.cpp
- Llama-Swap
- Compatibile OpenAI generico, per endpoint locali o self-hosted come `vLLM` o `LocalAI`

Valori di default in [config.json](E:\AI_Assistant.claude\config.json):

- `Ollama`: `http://localhost:11434`
- `LM Studio`: `http://localhost:1234/v1`
- `Llama.cpp`: `http://localhost:8033/v1`
- `Llama-Swap`: `http://localhost:8080/v1`

Puoi modificarli direttamente dall'interfaccia, senza toccare i file a mano.

## 📋 Requisiti

### Per usare il setup Windows

- 🪟 Windows 10 o Windows 11
- 🧠 Almeno un backend locale attivo tra quelli supportati, se vuoi usare davvero l'assistente
- 🎮 GPU consigliata per un uso più fluido con modelli vision o multimodali

`Python non serve`: il setup include gia tutto il necessario per avviare l'app.

### Per eseguire il progetto da sorgente

- 🪟 Windows 10 o Windows 11
- 🐍 Python 3.10 o superiore gia installato nel sistema
- 🧠 Almeno un backend locale attivo tra quelli supportati
- 🎮 GPU consigliata per un uso più fluido con modelli vision o multimodali

## 📦 Installazione da sorgente

Questa sezione serve solo se vuoi clonare il repository e avviare il progetto manualmente.

1. Clona o scarica il repository.
2. Esegui [setup.bat](E:\AI_Assistant.claude\setup.bat).
3. Attendi la creazione del `venv` e l'installazione delle dipendenze.
4. Avvia l'app con `start_ai_assistant.bat`.

Se preferisci farlo manualmente:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\pythonw.exe main.py
```

## 📚 Dipendenze principali

Le dipendenze Python sono in [requirements.txt](E:\AI_Assistant.claude\requirements.txt):

- `pyqt6`
- `pyqt6-webengine`
- `ollama`
- `requests`
- `pyperclip`
- `pyautogui`
- `mss`
- `pillow`
- `markdown`
- `openai`

## 🧭 Come si usa

1. Avvia l'app.
2. Cerca l'icona nella system tray.
3. Con click destro puoi:
   - 💬 aprire la chat
   - 🤖 scegliere backend e modello
   - 📸 analizzare un'area dello schermo
   - 📋 analizzare il testo copiato
   - ⚙️ aprire la configurazione dei backend
4. Dopo una cattura o un'analisi, continua la conversazione in chat per fare follow-up.

## 💾 Persistenza e file locali

Il progetto salva dati locali in questi file:

- [config.json](E:\AI_Assistant.claude\config.json): URL dei backend
- [chat_history.db](E:\AI_Assistant.claude\chat_history.db): cronologia chat persistente
- [history_db.json](E:\AI_Assistant.claude\history_db.json): storico legacy o dati precedenti

`chat_history.db` è ignorato dal repository e non dovrebbe essere versionato.

## 🗂️ Struttura del repository

- [main.py](E:\AI_Assistant.claude\main.py): applicazione principale
- [requirements.txt](E:\AI_Assistant.claude\requirements.txt): dipendenze Python
- [config.json](E:\AI_Assistant.claude\config.json): configurazione backend
- [setup.bat](E:\AI_Assistant.claude\setup.bat): bootstrap ambiente su Windows
- [ai_assistant.ico](E:\AI_Assistant.claude\ai_assistant.ico): icona dell'app
- [README.md](E:\AI_Assistant.claude\README.md): documentazione progetto

## 🧪 Note tecniche

- La shell dell'app è costruita in **PyQt6**.
- La chat `v3.4` usa una **webview** (`PyQt6-WebEngine`) per ottenere una UI più moderna e flessibile.
- Le sessioni sono memorizzate in **SQLite**.
- Per i backend OpenAI-compatible locali viene usato il client `openai` con `base_url` custom.
- Per Ollama viene usata l'integrazione Python dedicata.
- `Analizza Area` sfrutta il **ritaglio nativo di Windows** per una resa migliore, soprattutto su sistemi HDR.

## ⬇️ Download eseguibile

Se preferisci una build pronta all'uso:

1. Vai su [Releases](https://github.com/zoott28354/ai_assistant/releases)
2. Scarica `AI_Assistant_Setup_v3.4.exe`
3. Installa l'app normalmente
4. Se Windows mostra SmartScreen, scegli **"Ulteriori informazioni"** e poi **"Esegui comunque"**

Il setup installa gia l'app con il proprio runtime: non e necessario installare Python separatamente.

## 👤 Autore

Creato e mantenuto da **zoott28354**.

## 📄 Licenza

Questo progetto è distribuito con licenza **MIT**.
Per il testo completo vedi [LICENSE](E:\AI_Assistant.claude\LICENSE).

## 📈 Stato del progetto

La `v3.4` è una versione più matura rispetto alla precedente `v3.2`, soprattutto per:

- 💬 UI chat
- 🗂️ gestione cronologia
- 🧱 stabilità del flusso di cattura
- 🌈 migliore integrazione con il ritaglio nativo di Windows

Se usi backend locali tutti i giorni sul desktop, questa versione punta a essere più affidabile, più leggibile e più comoda nell'uso reale, non solo in demo.
