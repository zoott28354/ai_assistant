import sys
import io
import time
import os
import base64
import requests
import pyperclip
import pyautogui
import ollama
import json
import re
import mss
import mss.tools
from PIL import Image
from datetime import datetime
from functools import partial
from openai import OpenAI

# --- CONFIGURAZIONE SISTEMA ---
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
HISTORY_FILE = "history_db.json"

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
                             QLineEdit, QPushButton, QLabel, QSystemTrayIcon, QMenu, 
                             QStyle, QRubberBand, QMessageBox)
from PyQt6.QtCore import Qt, QRect, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

# --- FUNZIONE PER RISORSE EXE ---
def resource_path(relative_path):
    """ Ottiene il percorso assoluto delle risorse, fondamentale per PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AIBackend:
    OLLAMA = "Ollama"
    LM_STUDIO = "LM Studio"
    LLAMA_CPP = "Llama.cpp"

# --- STILE WINDOWS 11 FLUENT ---
STYLE_SHEET = """
    QWidget { 
        background-color: #1a1a1a; 
        color: #f0f0f0; 
        font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif; 
    }
    QTextBrowser { 
        background-color: #262626; 
        border: 1px solid #333; 
        border-radius: 12px; 
        padding: 15px; 
        font-size: 14px; 
        color: #e0e0e0;
    }
    QLineEdit { 
        background-color: #333; 
        border: 1px solid #444; 
        padding: 12px; 
        border-radius: 8px; 
        color: #ffffff; 
        font-size: 14px;
    }
    QLineEdit:focus { border: 1px solid #0078d4; background-color: #3d3d3d; }
    QPushButton { 
        background-color: #0078d4; 
        color: white; 
        border: none; 
        padding: 10px 20px; 
        border-radius: 8px; 
        font-weight: 600; 
    }
    QPushButton:hover { background-color: #1085e0; }
    QMenu { 
        background-color: #2b2b2b; 
        border: 1px solid #444; 
        border-radius: 8px; 
    }
    QMenu::item { padding: 8px 25px; color: white; }
    QMenu::item:selected { background-color: #0078d4; }
"""

def format_ai_response(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b style="color: #ffca28;">\1</b>', text)
    lines = text.split('\n')
    formatted_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('* ') or stripped.startswith('- '):
            content = stripped[2:]
            formatted_lines.append(f"<div style='margin-left: 20px; color: #e0e0e0;'><span style='color: #4fc3f7;'>•</span> {content}</div>")
        elif re.match(r'^\d+\.', stripped):
            formatted_lines.append(f"<div style='margin-left: 20px; color: #e0e0e0;'><span style='color: #81c784;'>{stripped}</span></div>")
        else:
            formatted_lines.append(line)
    return '<br>'.join(formatted_lines)

class AIWorker(QThread):
    finished = pyqtSignal(str, list)
    def __init__(self, history, model, backend):
        super().__init__()
        self.history, self.model, self.backend = history, model, backend

    def run(self):
        try:
            if self.backend == AIBackend.OLLAMA:
                res = ollama.chat(model=self.model, messages=self.history)
                answer = res['message']['content']
            else:
                base_url = "http://localhost:1234/v1" if self.backend == AIBackend.LM_STUDIO else "http://localhost:8033/v1"
                client = OpenAI(base_url=base_url, api_key="sk-no-key-required")
                msgs = []
                for m in self.history:
                    if 'images' in m and m['images']:
                        content = [{"type": "text", "text": m['content']}]
                        for img in m['images']:
                            b64 = img if isinstance(img, str) else base64.b64encode(img).decode('utf-8')
                            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
                        msgs.append({"role": m['role'], "content": content})
                    else:
                        msgs.append({"role": m['role'], "content": m['content']})
                comp = client.chat.completions.create(model=self.model, messages=msgs)
                answer = comp.choices[0].message.content
            self.history.append({'role': 'assistant', 'content': answer})
            self.finished.emit(answer, self.history)
        except Exception as e:
            self.finished.emit(f"Errore [{self.backend}]: {str(e)}", self.history)

class SnippingTool(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.3)
        self.rubberband = QRubberBand(QRubberBand.Shape.Rectangle, self)
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())
        self.pixel_ratio = screen.devicePixelRatio()
        self.show()

    def mousePressEvent(self, e):
        self.start_pt = e.pos()
        self.rubberband.setGeometry(QRect(self.start_pt, self.start_pt))
        self.rubberband.show()

    def mouseMoveEvent(self, e):
        self.rubberband.setGeometry(QRect(self.start_pt, e.pos()).normalized())

    def mouseReleaseEvent(self, e):
        r = QRect(self.start_pt, e.pos()).normalized()
        self.rubberband.hide()
        self.close()
        if r.width() > 5:
            QApplication.processEvents()
            time.sleep(0.2)
            x, y, w, h = int(r.x()*self.pixel_ratio), int(r.y()*self.pixel_ratio), int(r.width()*self.pixel_ratio), int(r.height()*self.pixel_ratio)
            with mss.mss() as sct:
                img_data = sct.grab({"top": y, "left": x, "width": w, "height": h})
                img = Image.frombytes("RGB", img_data.size, img_data.bgra, "raw", "BGRX")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                self.callback(buf.getvalue(), False)

class ChatWindow(QWidget):
    history_updated = pyqtSignal(int, list)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant - Versione 2.1.1 - EXE Icon Fix")
        self.resize(550, 750)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet(STYLE_SHEET)
        layout = QVBoxLayout()
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        layout.addWidget(self.chat_display)
        self.status_label = QLabel("Pronto")
        layout.addWidget(self.status_label)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Chiedi all'AI...")
        self.input_field.returnPressed.connect(self.send_msg)
        layout.addWidget(self.input_field)
        self.setLayout(layout)
        self.history, self.idx, self.model, self.backend = [], -1, "", ""

    def load_session(self, idx, hist, model, backend, is_new=False):
        self.idx, self.history, self.model, self.backend = idx, hist, model, backend
        self.chat_display.clear()
        for m in self.history:
            self.append_view("AI" if m['role']=='assistant' else "Tu", m['content'])
        self.show()
        if is_new: self.ask_ai()

    def send_msg(self):
        txt = self.input_field.text().strip()
        if txt:
            self.history.append({'role': 'user', 'content': txt})
            self.append_view("Tu", txt)
            self.input_field.clear()
            self.ask_ai()
            self.history_updated.emit(self.idx, self.history)

    def ask_ai(self):
        self.status_label.setText(f"🧠 {self.model} via {self.backend}...")
        self.worker = AIWorker(list(self.history), self.model, self.backend)
        self.worker.finished.connect(self.on_res)
        self.worker.start()

    def on_res(self, text, hist):
        self.history = hist
        self.append_view("AI", text)
        self.status_label.setText("Pronto")
        self.history_updated.emit(self.idx, self.history)

    def append_view(self, sender, text):
        color = "#4fc3f7" if sender == "AI" else "#81c784"
        formatted_text = format_ai_response(text)
        html = f"<div style='margin-bottom: 20px;'><b style='color:{color}; font-size: 15px;'>{sender}:</b><br><div style='margin-top: 5px; color: #ffffff;'>{formatted_text}</div></div><hr style='border: 0; border-top: 1px solid #333;'>"
        self.chat_display.append(html)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.active_backend = AIBackend.OLLAMA
        self.active_model = ""
        self.sessions = []
        self.load_history_from_disk()
        self.chat_window = ChatWindow()
        self.chat_window.history_updated.connect(self.save_updated_history)
        
        # Gestione Icona (Sia Tray che Finestra)
        icon_path = resource_path("ai_assistant.ico")
        self.app_icon = QIcon(icon_path) if os.path.exists(icon_path) else self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(self.app_icon)
        self.chat_window.setWindowIcon(self.app_icon)
        
        self.refresh_mods()
        self.update_menu()
        self.tray.show()

    def load_history_from_disk(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for s in loaded:
                        for m in s['history']:
                            if 'images' in m: m['images'] = [base64.b64decode(img) for img in m['images']]
                    self.sessions = loaded
            except: pass

    def save_updated_history(self, i, h):
        if i >= len(self.sessions): return
        self.sessions[i]['history'] = h
        temp_sessions = []
        for s in self.sessions:
            session_copy = json.loads(json.dumps(s, default=lambda x: None))
            session_copy['history'] = []
            for m in s['history']:
                m_copy = m.copy()
                if 'images' in m_copy: m_copy['images'] = [base64.b64encode(img).decode('utf-8') if isinstance(img, bytes) else img for img in m_copy['images']]
                session_copy['history'].append(m_copy)
            temp_sessions.append(session_copy)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(temp_sessions, f, indent=4, ensure_ascii=False)

    def refresh_mods(self):
        try:
            if self.active_backend == AIBackend.OLLAMA: ms = [m['model'] if isinstance(m, dict) else m.model for m in ollama.list().get('models', [])]
            elif self.active_backend == AIBackend.LM_STUDIO: ms = [m['id'] for m in requests.get("http://localhost:1234/v1/models").json()['data']]
            elif self.active_backend == AIBackend.LLAMA_CPP: ms = [m['id'] for m in requests.get("http://localhost:8033/v1/models").json()['data']]
            if ms:
                if self.active_model not in ms: self.active_model = ms[0]
            return ms
        except: return ["Offline"]

    def update_menu(self):
        m = QMenu()
        m.addAction("📸 Analizza Area (Rettangolo)", self.start_vision)
        m.addAction("📋 Analizza Testo Copiato", self.start_text_grab)
        m.addSeparator()
        bk = m.addMenu("⚙️ Motore AI")
        for b in [AIBackend.OLLAMA, AIBackend.LM_STUDIO, AIBackend.LLAMA_CPP]:
            a = bk.addAction(b); a.setCheckable(True); a.setChecked(self.active_backend == b)
            a.triggered.connect(partial(self.set_bk, b))
        mods = self.refresh_mods()
        mm = m.addMenu(f"🤖 Modelli")
        for x in mods:
            a = mm.addAction(x); a.setCheckable(True); a.setChecked(self.active_model == x)
            a.triggered.connect(partial(self.set_mod, x))
        m.addSeparator()
        st = m.addMenu("📜 Storico Chat")
        if not self.sessions: st.addAction("(Vuoto)").setEnabled(False)
        for i, s in enumerate(reversed(self.sessions)):
            idx = len(self.sessions)-1-i
            st.addAction(s['label']).triggered.connect(partial(self.restore, idx))
        m.addSeparator()
        m.addAction("🗑️ Svuota Tutto", self.clear_all_history)
        m.addSeparator()
        m.addAction("❌ Esci", self.app.quit)
        self.tray.setContextMenu(m)

    def clear_all_history(self):
        if QMessageBox.question(None, 'Conferma', "Cancellare tutta la cronologia?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.sessions = []; self.update_menu()
            if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)

    def set_bk(self, b): self.active_backend = b; self.refresh_mods(); self.update_menu()
    def set_mod(self, x): self.active_model = x; self.update_menu()
    def start_vision(self): self.snipper = SnippingTool(self.process)
    def start_text_grab(self):
        self.tray.contextMenu().hide(); QApplication.processEvents(); time.sleep(0.4)
        pyautogui.hotkey('ctrl', 'c'); time.sleep(0.3)
        txt = pyperclip.paste()
        if txt.strip(): self.process(f"Analizza e spiega questo testo in italiano:\n\n{txt}", True)

    def process(self, data, is_txt):
        idx = len(self.sessions)
        if is_txt: hist = [{'role': 'user', 'content': data}]
        else:
            p = "Analizza questa immagine. Se vedi testo, traducilo in italiano. Spiega errori o codice. Rispondi in italiano."
            hist = [{'role': 'user', 'content': p, 'images': [data]}]
        self.sessions.append({'label': f"Sess {idx+1} ({datetime.now().strftime('%d/%m %H:%M')})", 'history': hist, 'model': self.active_model, 'backend': self.active_backend})
        self.save_updated_history(idx, hist); self.update_menu()
        self.chat_window.load_session(idx, hist, self.active_model, self.active_backend, is_new=True)

    def restore(self, i):
        s = self.sessions[i]
        self.chat_window.load_session(i, s['history'], s['model'], s['backend'])

    def run(self): sys.exit(self.app.exec())

if __name__ == "__main__":
    MainApp().run()