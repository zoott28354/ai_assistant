# 👁️ AI Assistant (v3.2)

Un potente assistente AI locale per Windows progettato per l'analisi visiva e testuale immediata. Grazie all'integrazione con i principali motori LLM locali, permette di estrarre informazioni da immagini, tradurre testi e spiegare codice direttamente dal tuo desktop, sfruttando la potenza della tua GPU (ottimizzato per serie RTX 50/40).



## ✨ Caratteristiche principali
* **Modern UI v3.2:** Nuova interfaccia chat con sidebar persistente per la cronologia e design minimalista.
* **Sistema di Configurazione:** Pannello dedicato per gestire gli URL dei backend (Ollama, LM Studio, ecc.) in modo persistente.
* **Analisi Area (Screenshot):** Seleziona un rettangolo sullo schermo per inviarlo all'AI.
* **Analisi Appunti (Clipboard):** Analizza, spiega o traduci istantaneamente il testo negli appunti.
* **Multi-Backend:** Supporto per Ollama, LM Studio, Llama.cpp e Llama-Swap.
* **Privacy Totale:** Tutto viene elaborato localmente, nessun dato viene inviato al cloud.
* **Storico Sessioni:** Conversazioni salvate automaticamente in `history_db.json`.

## 🛠️ Requisiti di Sistema
* **Sistema Operativo:** Windows 10/11.
* **Python:** 3.10 o superiore.
* **AI Engine:** Uno tra Ollama, LM Studio o Llama.cpp attivo.
* **Hardware:** Consigliata GPU NVIDIA (es. RTX 5090/4070).

---

## 📦 Download Eseguibile (Consigliato)
Se non desideri installare Python, scarica la versione pronta all'uso:

1. Vai nella sezione **[Releases](https://github.com/zoott28354/ai_assistant/releases)**.
2. Scarica il file **`AI_Assistant_v3.2.exe`**.
3. **Avviso Windows:** Clicca su *"Ulteriori informazioni"* e poi su *"Esegui comunque"*.

---

## 🚀 Installazione da Sorgente (Sviluppatori)
1. Scarica o clona questo repository.
2. Clicca due volte su **`setup.bat`**.
3. Avvia il programma con **`start_ai_assistant.bat`**.

---

## 🖥️ Come iniziare
1. Avvia l'app e cerca l'icona dell'occhio nella **System Tray**.
2. Fai click destro per configurare backend e modelli.
3. Usa la shortcut di cattura o analisi testo dal menu.

## 📂 Struttura del Repository
* `main.py`: Sorgente principale.
* `config.json`: Configurazione backend.
* `setup.bat`: Configurazione ambiente.
* `requirements.txt`: Dipendenze.
* `ai_assistant.ico`: Icona ufficiale.

---
*Progetto focalizzato su privacy e velocità nell'uso quotidiano dei modelli LLM locali.*