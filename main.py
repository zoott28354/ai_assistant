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
import markdown
from PIL import Image
from datetime import datetime
from functools import partial
from openai import OpenAI

# --- CONFIGURAZIONE SISTEMA ---
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
HISTORY_FILE = "history_db.json"
CONFIG_FILE = "config.json"

# Default backend URLs
DEFAULT_CONFIG = {
    "backends": {
        "Ollama": "http://localhost:11434",
        "LM Studio": "http://localhost:1234/v1",
        "Llama.cpp": "http://localhost:8033/v1",
        "Llama-Swap": "http://localhost:8080/v1"
    }
}

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
                             QLineEdit, QPushButton, QLabel, QSystemTrayIcon, QMenu, 
                             QStyle, QRubberBand, QMessageBox, QListWidget, QListWidgetItem, 
                             QScrollArea, QFrame, QSizePolicy, QAbstractItemView, QDialog, 
                             QFormLayout, QDialogButtonBox)
from PyQt6.QtCore import Qt, QRect, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor

# --- FUNZIONE PER RISORSE EXE ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AIBackend:
    OLLAMA = "Ollama"
    LM_STUDIO = "LM Studio"
    LLAMA_CPP = "Llama.cpp"
    LLAMA_SWAP = "Llama-Swap"

# --- STILE WINDOWS 11 FLUENT MODERN ---
STYLE_SHEET = """
    QWidget { 
        background-color: #1a1a1a; 
        color: #d4d4d4; 
        font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif; 
    }
    
    /* SIDEBAR */
    QListWidget {
        background-color: #181818;
        border-right: 1px solid #2a2a2a;
        outline: none;
        padding-top: 10px;
    }
    QListWidget::item {
        color: #b0b0b0;
        padding: 12px 15px;
        margin: 4px 8px;
        border-radius: 8px;
    }
    QListWidget::item:hover {
        background-color: #2a2a2a;
        color: white;
    }
    QListWidget::item:selected {
        background-color: #353535;
        color: white;
        border-left: 3px solid #60cdff;
    }

    /* CHAT AREA */
    QScrollArea {
        border: none;
        background-color: #1a1a1a;
    }
    
    /* INPUT */
    QLineEdit { 
        background-color: #2d2d2d; 
        border: 1px solid #3d3d3d; 
        padding: 12px 18px; 
        border-radius: 22px; 
        color: #ffffff; 
        font-size: 14px;
        margin: 10px;
    }
    QLineEdit:focus { border: 1px solid #60cdff; background-color: #323232; }
    
    QPushButton { 
        background-color: #60cdff; 
        color: #000000; 
        border: none; 
        padding: 8px 16px; 
        border-radius: 6px; 
        font-weight: 600; 
    }
    QPushButton:hover { background-color: #7ad6ff; }

    /* MENU */
    QMenu { 
        background-color: #2b2b2b; 
        border: 1px solid #444; 
        border-radius: 8px; 
    }
    QMenu::item { padding: 8px 25px; color: white; }
    QMenu::item:selected { background-color: #60cdff; color: black; }
"""

class MessageWidget(QWidget):
    def __init__(self, role, content, images=None):
        super().__init__()
        self.role = role
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 8, 15, 8) # Outer margins
        
        # Minimalist Container Config (no bubbles, just rectangles)
        container = QFrame()
        container.setObjectName("msg_container")
        
        if role == 'user':
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bg_color = "#2a2a2a" # Dark grey for user
            text_color = "#e8e8e8"
            border_radius = "4px" # Minimal rounding
            lbl_align = Qt.AlignmentFlag.AlignLeft
            label_text = "" # No label
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bg_color = "#1e1e1e" # Even darker for AI
            text_color = "#d4d4d4"
            border_radius = "4px"
            lbl_align = Qt.AlignmentFlag.AlignLeft
            label_text = ""

        container.setStyleSheet(f"""
            #msg_container {{ 
                background-color: {bg_color}; 
                border-radius: {border_radius}; 
                padding: 16px; 
                border-left: 2px solid {"#4a9eff" if role == "user" else "#3a3a3a"};
            }}
        """)
        
        # Full width for minimalist design
        container.setMinimumWidth(200)

        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(5,5,5,5)
        clayout.setSpacing(8)

        # Role Label (Optional, maybe only for AI)
        if label_text:
            lbl_role = QLabel(label_text)
            lbl_role.setStyleSheet(f"color: #aaaaaa; font-weight: bold; font-size: 10px; margin-bottom: 2px;")
            clayout.addWidget(lbl_role)

        # Images
        if images:
            for img_data in images:
                try:
                    if isinstance(img_data, str): img_bytes = base64.b64decode(img_data)
                    else: img_bytes = img_data
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_bytes)
                    if not pixmap.isNull():
                        if pixmap.width() > 500: pixmap = pixmap.scaledToWidth(500, Qt.TransformationMode.SmoothTransformation)
                        img_lbl = QLabel()
                        img_lbl.setPixmap(pixmap)
                        # Rounded corners for images too
                        mask = QPixmap(pixmap.size())
                        mask.fill(Qt.GlobalColor.transparent)
                        p = QPainter(mask)
                        p.setRenderHint(QPainter.RenderHint.Antialiasing)
                        p.setBrush(QColor("black"))
                        p.drawRoundedRect(0, 0, pixmap.width(), pixmap.height(), 12, 12)
                        p.end()
                        # This image rounding is complex without more code, let's skip mask for now but add style
                        img_lbl.setStyleSheet("border-radius: 8px;")
                        clayout.addWidget(img_lbl)
                except Exception: pass

        # Text Content
        formatted_html = self.format_text(content)
        lbl_text = QLabel(formatted_html)
        lbl_text.setWordWrap(True)
        lbl_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        # Use white for user, slightly off-white for AI
        lbl_text.setStyleSheet(f"color: {text_color}; font-size: 14px; selection-background-color: #ffffff; selection-color: #000000;")
        
        clayout.addWidget(lbl_text)
        layout.addWidget(container)
        self.setLayout(layout)

    def format_text(self, text):
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'`(.*?)`', r'<code style="background-color: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 4px;">\1</code>', text)
        text = re.sub(r'```(.*?)```', r'<pre style="background-color: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px;">\1</pre>', text, flags=re.DOTALL)
        text = text.replace('\n', '<br>')
        return text

class AIWorker(QThread):
    finished = pyqtSignal(str, list)
    def __init__(self, history, model, backend, backend_urls):
        super().__init__()
        self.history, self.model, self.backend = history, model, backend
        self.backend_urls = backend_urls

    def run(self):
        try:
            if self.backend == AIBackend.OLLAMA:
                # Fix: stream=False è fondamentale per non bloccare il programma
                res = ollama.chat(model=self.model, messages=self.history, stream=False)
                answer = res['message']['content']
            else:
                base_url = self.backend_urls.get("backends", {}).get(self.backend, "")
                if not base_url:
                    raise Exception(f"URL non configurato per {self.backend}")
                
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

class ConfigDialog(QDialog):
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurazione Backend LLM")
        self.resize(500, 300)
        # Use standard dialog flags
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowSystemMenuHint | Qt.WindowType.WindowCloseButtonHint)
        
        # Simple neutral style
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: white; }
            QLabel { color: white; }
            QLineEdit { background-color: #3d3d3d; color: white; border: 1px solid #555; padding: 5px; }
            QPushButton { background-color: #0078d4; color: white; padding: 6px 15px; border-radius: 4px; }
        """)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.inputs = {}
        for name, url in current_config["backends"].items():
            edit = QLineEdit(url)
            self.inputs[name] = edit
            form_layout.addRow(QLabel(f"{name}:"), edit)
            
        layout.addLayout(form_layout)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_config(self):
        return {"backends": {n: e.text().strip() for n, e in self.inputs.items()}}

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

class OllamaChatWindow(QWidget):
    history_updated = pyqtSignal(int, list)
    session_selected = pyqtSignal(int)
    new_chat_requested = pyqtSignal()

    def __init__(self, backend_urls):
        super().__init__()
        self.setWindowTitle("AI Assistant - v3.2")
        self.resize(900, 700) # Bigger window for sidebar
        self.setStyleSheet(STYLE_SHEET)
        self.backend_urls = backend_urls
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # --- LEFT SIDEBAR ---
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_container = QWidget()
        self.sidebar_container.setFixedWidth(220)
        self.sidebar_container.setStyleSheet("background-color: #171717; border-right: 1px solid #333;")
        self.sidebar_container.setLayout(self.sidebar_layout)
        
        # New Chat Button
        self.btn_new = QPushButton("+ Nuova Chat")
        self.btn_new.setStyleSheet("background-color: #f0f0f0; color: black; margin: 10px; padding: 8px;")
        self.btn_new.clicked.connect(self.new_chat_requested.emit)
        self.sidebar_layout.addWidget(self.btn_new)

        # History List
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(lambda item: self.session_selected.emit(item.data(Qt.ItemDataRole.UserRole)))
        self.sidebar_layout.addWidget(self.history_list)
        
        main_layout.addWidget(self.sidebar_container)

        # --- RIGHT CHAT AREA ---
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0,0,0,0)
        
        # Scroll Area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.scroll_vbox = QVBoxLayout(self.scroll_content)
        self.scroll_vbox.setSpacing(15)
        self.scroll_vbox.addStretch() # Push messages down
        self.scroll_area.setWidget(self.scroll_content)
        
        chat_layout.addWidget(self.scroll_area)
        
        # Input Area - Fixed at bottom
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Scrivi un messaggio... (Incolla immagini con Ctrl+V)")
        self.input_field.returnPressed.connect(self.send_msg)
        
        input_layout.addWidget(self.input_field)
        chat_layout.addWidget(self.status_label)
        chat_layout.addWidget(input_container)

        main_layout.addLayout(chat_layout)

        self.history, self.idx, self.model, self.backend = [], -1, "", ""


    def update_sidebar(self, sessions, current_idx=-1):
        self.history_list.clear()
        for i, s in enumerate(reversed(sessions)):
            real_idx = len(sessions) - 1 - i
            item = QListWidgetItem(s.get('label', f"Sess {real_idx+1}"))
            item.setData(Qt.ItemDataRole.UserRole, real_idx)
            self.history_list.addItem(item)
            if real_idx == current_idx:
                item.setSelected(True)

    def load_session(self, idx, hist, model, backend, is_new=False):
        self.idx, self.history, self.model, self.backend = idx, hist, model, backend
        
        # Clear chat area
        while self.scroll_vbox.count() > 1: # Keep the stretch item
            child = self.scroll_vbox.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        # Repopulate
        for m in self.history:
            self.add_message_bubble(m['role'], m['content'], m.get('images', []))
            
        self.show()
        if is_new: self.ask_ai()
        
        # Update status
        self.status_label.setText(f"Modello: {model} | Backend: {backend}")

    def add_message_bubble(self, role, content, images=[]):
        bubble = MessageWidget(role, content, images)
        self.scroll_vbox.insertWidget(self.scroll_vbox.count()-1, bubble)
        # Auto scroll to bottom
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def send_msg(self):
        txt = self.input_field.text().strip()
        if txt:
            self.history.append({'role': 'user', 'content': txt})
            self.add_message_bubble("user", txt)
            self.input_field.clear()
            self.ask_ai()
            self.history_updated.emit(self.idx, self.history)

    def ask_ai(self):
        self.status_label.setText(f"Generazione in corso con {self.model}...")
        self.worker = AIWorker(list(self.history), self.model, self.backend, self.backend_urls)
        self.worker.finished.connect(self.on_res)
        self.worker.start()

    def on_res(self, text, hist):
        self.history = hist
        self.add_message_bubble("assistant", text)
        self.status_label.setText(f"Pronto ({self.model})")
        self.history_updated.emit(self.idx, self.history)


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.active_backend = AIBackend.OLLAMA
        self.active_model = ""
        self.sessions = []
        
        # Load configuration
        self.backend_urls = self.load_config()
        
        self.load_history_from_disk()
        
        self.chat_window = OllamaChatWindow(self.backend_urls)
        self.chat_window.history_updated.connect(self.save_updated_history)
        self.chat_window.session_selected.connect(self.restore)
        self.chat_window.new_chat_requested.connect(self.start_new_session_ui)
        
        # Initial Sidebar Population
        self.chat_window.update_sidebar(self.sessions)

        # Gestione Icona (Sia Tray che Finestra)
        icon_path = resource_path("ai_assistant.ico")
        self.app_icon = QIcon(icon_path) if os.path.exists(icon_path) else self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(self.app_icon)
        self.chat_window.setWindowIcon(self.app_icon)
        
        self.refresh_mods()
        self.update_menu()
        self.tray.show()

    def start_new_session_ui(self):
        # Starts a temporary empty session visible in UI but not saved until first message
        # Implementation shortcut: reuse process() with empty data? 
        # Actually better to just clear UI and set idx to new.
        # But for now let's just create a new 'Welcome' session to keep it simple
        self.process("Ciao! Come posso aiutarti oggi?", True)

    def load_config(self):
        """Load backend configuration from config.json or return defaults"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return DEFAULT_CONFIG.copy()
    
    def save_config(self, config):
        """Save backend configuration to config.json"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.backend_urls = config
            QMessageBox.information(None, "Configurazione", "Configurazione salvata con successo!")
        except Exception as e:
            QMessageBox.warning(None, "Errore", f"Errore nel salvataggio: {str(e)}")
    
    def open_config_dialog(self):
        """Open configuration dialog"""
        # Close search menu to avoid focus issues
        self.tray.contextMenu().hide()
        
        # Create dialog with chat_window as parent if it exists to improve centering
        parent = self.chat_window if self.chat_window.isVisible() else None
        dialog = ConfigDialog(self.backend_urls, parent)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            self.save_config(new_config)
            self.refresh_mods()
            self.update_menu()

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
        
        # Update sidebar labels if changed (e.g. first message could be title)
        # self.chat_window.update_sidebar(self.sessions, i) 

    def refresh_mods(self):
        try:
            if self.active_backend == AIBackend.OLLAMA: 
                ms = [m['model'] if isinstance(m, dict) else m.model for m in ollama.list().get('models', [])]
            else:
                # Use configured URL
                base_url = self.backend_urls.get("backends", {}).get(self.active_backend, "")
                if not base_url:
                    return ["URL non configurato"]
                ms = [m['id'] for m in requests.get(f"{base_url.rstrip('/v1')}/v1/models").json()['data']]
            if ms:
                if self.active_model not in ms: self.active_model = ms[0]
            return ms
        except: return ["Offline"]

    def update_menu(self):
        m = QMenu()
        m.addAction("📸 Analizza Area (Rettangolo)", self.start_vision)
        m.addAction("📋 Analizza Testo Copiato", self.start_text_grab)
        m.addSeparator()
        m.addAction("💬 Apri Chat", self.chat_window.show)
        m.addSeparator()
        m.addAction("⚙️ Configura Backend", self.open_config_dialog)
        m.addSeparator()
        bk = m.addMenu("⚙️ Motore AI")
        for b in [AIBackend.OLLAMA, AIBackend.LM_STUDIO, AIBackend.LLAMA_CPP, AIBackend.LLAMA_SWAP]:
            a = bk.addAction(b); a.setCheckable(True); a.setChecked(self.active_backend == b)
            a.triggered.connect(partial(self.set_bk, b))
        mods = self.refresh_mods()
        mm = m.addMenu(f"🤖 Modelli")
        for x in mods:
            a = mm.addAction(x); a.setCheckable(True); a.setChecked(self.active_model == x)
            a.triggered.connect(partial(self.set_mod, x))
        m.addSeparator()
        m.addAction("❌ Esci", self.app.quit)
        self.tray.setContextMenu(m)

    def clear_all_history(self):
        if QMessageBox.question(None, 'Conferma', "Cancellare tutta la cronologia?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.sessions = []; self.chat_window.update_sidebar([])
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
        self.save_updated_history(idx, hist) 
        self.chat_window.update_sidebar(self.sessions, idx)
        self.chat_window.load_session(idx, hist, self.active_model, self.active_backend, is_new=True)

    def restore(self, i):
        s = self.sessions[i]
        self.chat_window.load_session(i, s['history'], s['model'], s['backend'])

    def run(self): sys.exit(self.app.exec())

if __name__ == "__main__":
    MainApp().run()