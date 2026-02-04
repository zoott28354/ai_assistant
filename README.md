# 👁️ AI Assistant (v3.1 - Fixed)

Un potente assistente AI locale per Windows progettato per l'analisi visiva e testuale immediata. Grazie all'integrazione con i principali motori LLM locali, permette di estrarre informazioni da immagini, tradurre testi e spiegare codice direttamente dal tuo desktop, sfruttando la potenza della tua GPU (ottimizzato per serie RTX 50/40).



## ✨ Caratteristiche principali
* **Modern UI v3.0:** Nuova interfaccia chat a bolle con sidebar per la cronologia.
* **Analisi Area (Screenshot):** Seleziona un rettangolo sullo schermo per inviarlo all'AI. Ideale per risolvere errori, analizzare grafici o tradurre porzioni di testo non selezionabili.
* **Analisi Appunti (Clipboard):** Analizza, spiega o traduci istantaneamente il testo che hai appena copiato negli appunti.
* **Multi-Backend:** Supporto nativo per:
    * **Ollama**
    * **LM Studio** (Porta 1234)
    * **Llama.cpp** (Porta predefinita: 8033)
    * **Llama-Swap** (Porta 8080)
* **Privacy Totale:** Nessun dato viene inviato al cloud. Tutto viene elaborato localmente.
* **Storico Sessioni:** Salva automaticamente le conversazioni in un database locale (`history_db.json`).

## 🛠️ Requisiti di Sistema
* **Sistema Operativo:** Windows 10/11.
* **Python:** 3.10 o superiore (necessario solo per l'installazione da sorgente).
* **AI Engine:** Uno tra Ollama, LM Studio o Llama.cpp attivo sul PC.
* **Hardware:** Consigliata GPU NVIDIA (es. RTX 5090/4070) per prestazioni ottimali.

---

## 📦 Download Eseguibile (Consigliato)
Se non desideri installare Python o gestire script, puoi scaricare la versione già compilata e pronta all'uso:

1. Vai nella sezione **[Releases](https://github.com/TUO_UTENTE/ai_assistant/releases)** di questo repository.
2. Scarica il file **`AI_Assistant_v3.0.exe`**.
3. **Avviso Windows:** Trattandosi di un software non firmato digitalmente, Windows Defender potrebbe mostrare un avviso. Clicca su *"Ulteriori informazioni"* e poi su *"Esegui comunque"*.

---

## 🚀 Installazione da Sorgente (Sviluppatori)
Se preferisci eseguire il codice Python direttamente o vuoi apportare modifiche:

1. Scarica o clona questo repository.
2. Clicca due volte sul file **`setup.bat`**. 
   * *Questo script creerà automaticamente l'ambiente virtuale (`venv`), installerà le librerie necessarie (`requirements.txt`) e genererà il lanciatore.*
3. Per avviare il programma, usa il file appena creato: **`start_ai_assistant.bat`**.



---

## 🖥️ Come iniziare
1. Avvia l'applicazione. L'icona dell'occhio apparirà nella **System Tray** (vicino all'orologio).
2. Fai click destro sull'icona per:
    * Selezionare il **Motore AI** attivo.
    * Scegliere il **Modello LLM** (assicurati che sia già caricato nel tuo motore AI).
3. Usa "Analizza Area" per catturare uno screenshot o "Analizza Testo" per processare gli appunti.

## 📂 Struttura del Repository
* `main.py`: Codice sorgente principale.
* `setup.bat`: Script di configurazione ambiente virtuale.
* `requirements.txt`: Dipendenze Python.
* `ai_assistant.ico`: Icona ufficiale del progetto.
* `.gitignore`: Filtro per evitare il caricamento di file pesanti o database privati.

---
*Progetto sviluppato per coniugare la potenza dei modelli LLM locali con un'esperienza utente fluida e immediata su Windows.*