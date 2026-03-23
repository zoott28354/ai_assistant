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
from PIL import Image, ImageEnhance, ImageStat, ImageOps, ImageGrab
from datetime import datetime
from functools import partial
from openai import OpenAI
import sqlite3

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
                             QFormLayout, QDialogButtonBox, QSplitter)
from PyQt6.QtCore import Qt, QRect, QThread, pyqtSignal, pyqtSlot, QObject, QSize, QTimer, QBuffer, QIODevice
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings


def normalize_hdr_capture(image):
    image = image.convert("RGB")
    luminance = image.convert("L")
    histogram = luminance.histogram()
    total_pixels = sum(histogram) or 1
    bright_ratio = sum(histogram[245:]) / total_pixels
    mean_luma = ImageStat.Stat(luminance).mean[0]
    cumulative = 0
    p90 = 255
    p98 = 255
    for idx, count in enumerate(histogram):
        cumulative += count
        if cumulative >= total_pixels * 0.90 and p90 == 255:
            p90 = idx
        if cumulative >= total_pixels * 0.98:
            p98 = idx
            break

    if mean_luma < 168 and bright_ratio < 0.07 and p98 < 242:
        return image

    severe = mean_luma > 190 or bright_ratio > 0.16 or p98 >= 248
    knee = max(150, min(210, p90 + (10 if severe else 18)))
    compression = 0.28 if severe else 0.42
    gamma = 1.18 if severe else 1.10

    def tone_curve(p):
        v = (p / 255.0) ** gamma
        mapped = int(v * 255)
        if mapped > knee:
            mapped = int(knee + (mapped - knee) * compression)
        if mapped > 245:
            mapped = int(245 + (mapped - 245) * 0.18)
        return max(0, min(255, mapped))

    image = image.point(tone_curve)
    image = ImageEnhance.Brightness(image).enhance(0.84 if severe else 0.92)
    image = ImageEnhance.Contrast(image).enhance(1.08 if severe else 1.04)
    image = ImageEnhance.Color(image).enhance(0.93 if severe else 0.97)
    image = ImageOps.autocontrast(image, cutoff=(0.5, 1.5))
    return image


def image_to_png_bytes(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

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

# --- STILE MODERNO WINDOWS 11 FLUENT ---
STYLE_SHEET = """
    QWidget {
        background-color: #15191f;
        color: #e8edf2;
        font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif;
    }

    QWidget#chat_root {
        background-color: #15191f;
    }

    QWidget#sidebar_container {
        background-color: #10151b;
        border-right: 1px solid #202833;
    }

    QLabel#brand_eyebrow {
        color: #8ea0b5;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    QLabel#brand_title {
        color: #f5f7fa;
        font-size: 24px;
        font-weight: 700;
    }

    QLabel#brand_caption {
        color: #8ea0b5;
        font-size: 12px;
        line-height: 1.4;
    }

    QLabel#section_label {
        color: #6f8398;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 10px 18px 0 18px;
    }

    QListWidget {
        background-color: transparent;
        border: none;
        outline: none;
        padding: 6px 10px 12px 10px;
    }

    QListWidget::item {
        color: #bed0e1;
        background-color: transparent;
        padding: 12px 14px;
        margin: 4px 0;
        border-radius: 12px;
        border: 1px solid transparent;
    }

    QListWidget::item:hover {
        background-color: #18202a;
        border: 1px solid #273241;
        color: #ffffff;
    }

    QListWidget::item:selected {
        background-color: #1f2936;
        border: 1px solid #35506d;
        color: #ffffff;
    }

    QWidget#chat_panel {
        background-color: #15191f;
    }

    QFrame#top_bar {
        background-color: #171d25;
        border-bottom: 1px solid #232d39;
    }

    QLabel#chat_title {
        color: #f5f7fa;
        font-size: 20px;
        font-weight: 700;
    }

    QLabel#chat_subtitle {
        color: #91a3b5;
        font-size: 12px;
    }

    QLabel#context_badge {
        background-color: #202b38;
        border: 1px solid #304153;
        border-radius: 12px;
        color: #d9e5f1;
        font-size: 11px;
        font-weight: 600;
        padding: 6px 10px;
    }

    QScrollArea {
        border: none;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #15191f, stop:0.55 #141a22, stop:1 #10161e);
    }

    QWidget#composer {
        background-color: #171d25;
        border-top: 1px solid #232d39;
    }

    QFrame#composer_card {
        background-color: #1c2430;
        border: 1px solid #2c3a4b;
        border-radius: 18px;
    }

    QLineEdit {
        background-color: transparent;
        border: none;
        padding: 14px 16px;
        color: #f3f7fb;
        font-size: 14px;
        min-height: 26px;
    }

    QLineEdit:focus {
        border: none;
    }

    QPushButton {
        background-color: #3a7bd5;
        color: #ffffff;
        border: none;
        padding: 10px 18px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 13px;
        min-width: 88px;
    }

    QPushButton:hover {
        background-color: #4a8ae1;
    }

    QPushButton:pressed {
        background-color: #2f68b4;
    }

    QPushButton#new_chat_button {
        background-color: #e8eef6;
        color: #0d1620;
        border-radius: 14px;
        padding: 12px 16px;
        font-size: 13px;
        font-weight: 700;
        margin: 6px 14px 8px 14px;
    }

    QPushButton#new_chat_button:hover {
        background-color: #ffffff;
    }

    QPushButton#send_button {
        min-width: 96px;
        margin: 8px;
    }

    QLabel#status_label {
        color: #7f92a6;
        font-size: 11px;
        padding-left: 6px;
    }

    QFrame#welcome_card {
        background-color: rgba(25, 32, 41, 0.92);
        border: 1px solid #293445;
        border-radius: 26px;
    }

    QLabel#welcome_eyebrow {
        color: #8ea0b5;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    QLabel#welcome_title {
        color: #f7f9fb;
        font-size: 28px;
        font-weight: 700;
    }

    QLabel#welcome_text {
        color: #a8b6c5;
        font-size: 14px;
        line-height: 1.5;
    }

    QLabel#welcome_feature {
        background-color: #131921;
        border: 1px solid #283445;
        border-radius: 16px;
        color: #d9e5f1;
        font-size: 13px;
        padding: 12px 14px;
    }

    QMenu {
        background-color: #20262e;
        border: 1px solid #394555;
        border-radius: 12px;
        padding: 6px 0;
        font-size: 13px;
    }

    QMenu::item {
        padding: 8px 24px;
        color: white;
        margin: 2px 6px;
        border-radius: 8px;
    }

    QMenu::item:selected {
        background-color: #3a7bd5;
        color: white;
    }

    QMenu::separator {
        height: 1px;
        background-color: #394555;
        margin: 6px 10px;
    }

    QScrollBar:vertical {
        background-color: transparent;
        width: 12px;
        margin: 8px 4px 8px 0;
    }

    QScrollBar::handle:vertical {
        background-color: #334150;
        border-radius: 6px;
        min-height: 28px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #445569;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QLabel {
        color: #a0aaba;
        font-size: 12px;
    }
"""

class MessageWidget(QWidget):
    def __init__(self, role, content, images=None):
        super().__init__()
        self.role = role
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 8, 28, 8)

        if role == 'user':
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            text_color = "#dfe8f2"
            meta_color = "#7fb0ff"
            label_text = "Tu"
            accent = "#2f6fca"
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            text_color = "#edf3f9"
            meta_color = "#91a3b5"
            label_text = "Assistente locale"
            accent = "#2b3440"

        container = QWidget()
        container.setMinimumWidth(260)
        container.setMaximumWidth(760)

        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(0, 0, 0, 0)
        clayout.setSpacing(8)

        lbl_role = QLabel(label_text)
        lbl_role.setStyleSheet(f"""
            color: {meta_color};
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        """)
        clayout.addWidget(lbl_role)

        accent_line = QFrame()
        accent_line.setFixedHeight(1)
        accent_line.setStyleSheet(f"background-color: {accent}; border: none;")
        clayout.addWidget(accent_line)

        if images:
            for img_data in images:
                try:
                    if isinstance(img_data, str):
                        img_bytes = base64.b64decode(img_data)
                    else:
                        img_bytes = img_data
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_bytes)
                    if not pixmap.isNull():
                        if pixmap.width() > 540:
                            pixmap = pixmap.scaledToWidth(540, Qt.TransformationMode.SmoothTransformation)
                        img_lbl = QLabel()
                        img_lbl.setPixmap(pixmap)
                        img_lbl.setStyleSheet("margin: 6px 0 2px 0;")
                        clayout.addWidget(img_lbl)
                except Exception:
                    pass

        formatted_html = self.format_text(content)
        lbl_text = QLabel()
        lbl_text.setWordWrap(True)
        lbl_text.setOpenExternalLinks(True)
        lbl_text.setTextFormat(Qt.TextFormat.RichText)
        lbl_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        lbl_text.setText(formatted_html)
        lbl_text.setStyleSheet(f"""
            color: {text_color};
            font-size: 14px;
            line-height: 1.55;
            padding-top: 2px;
        """)
        clayout.addWidget(lbl_text)
        layout.addWidget(container)
        self.setLayout(layout)

    def format_text(self, text):
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'`(.*?)`', r'<code style="background-color: #202a36; padding: 2px 5px; border-radius: 4px; color: #8ec5ff;">\1</code>', text)
        text = re.sub(r'```(.*?)```', r'<pre style="background-color: #121821; border: 1px solid #263241; padding: 10px; border-radius: 12px; color: #e4ecf5; font-family: Consolas, monospace; white-space: pre-wrap;">\1</pre>', text, flags=re.DOTALL)
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
        self.screen = QApplication.primaryScreen()
        self.virtual_geometry = self.screen.virtualGeometry()
        self.setGeometry(self.virtual_geometry)
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
            global_top_left = self.mapToGlobal(r.topLeft())
            global_bottom_right = self.mapToGlobal(r.bottomRight())
            global_rect = QRect(global_top_left, global_bottom_right).normalized()

            try:
                grabbed = ImageGrab.grab(
                    bbox=(
                        global_rect.x(),
                        global_rect.y(),
                        global_rect.x() + global_rect.width(),
                        global_rect.y() + global_rect.height(),
                    ),
                    all_screens=True,
                )
                if grabbed:
                    self.callback(image_to_png_bytes(normalize_hdr_capture(grabbed)), False)
                    return
            except Exception:
                pass

            target_screen = QApplication.screenAt(global_rect.center()) or self.screen
            screen_rect = target_screen.geometry()
            local_rect = QRect(
                global_rect.x() - screen_rect.x(),
                global_rect.y() - screen_rect.y(),
                global_rect.width(),
                global_rect.height(),
            )

            pixmap = target_screen.grabWindow(0, local_rect.x(), local_rect.y(), local_rect.width(), local_rect.height())
            if not pixmap.isNull():
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                pixmap.save(buffer, "PNG")
                img = Image.open(io.BytesIO(bytes(buffer.data())))
                self.callback(image_to_png_bytes(normalize_hdr_capture(img)), False)
                return

            with mss.mss() as sct:
                img_data = sct.grab({
                    "top": global_rect.y(),
                    "left": global_rect.x(),
                    "width": global_rect.width(),
                    "height": global_rect.height()
                })
                img = Image.frombytes("RGB", img_data.size, img_data.bgra, "raw", "BGRX")
                self.callback(image_to_png_bytes(normalize_hdr_capture(img)), False)

class OllamaChatWindow(QWidget):
    history_updated = pyqtSignal(int, list)
    session_selected = pyqtSignal(int)
    new_chat_requested = pyqtSignal()

    def __init__(self, backend_urls):
        super().__init__()
        self.setWindowTitle("AI Assistant - v3.3")
        self.resize(1120, 760)
        self.setStyleSheet(STYLE_SHEET)
        self.backend_urls = backend_urls
        self.setObjectName("chat_root")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(8)
        self.splitter.setChildrenCollapsible(False)
        main_layout.addWidget(self.splitter)

        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(0, 0, 0, 14)
        self.sidebar_layout.setSpacing(0)
        self.sidebar_container = QWidget()
        self.sidebar_container.setObjectName("sidebar_container")
        self.sidebar_container.setMinimumWidth(260)
        self.sidebar_container.setMaximumWidth(420)
        self.sidebar_container.setLayout(self.sidebar_layout)
        self.splitter.addWidget(self.sidebar_container)

        brand_block = QWidget()
        brand_layout = QVBoxLayout(brand_block)
        brand_layout.setContentsMargins(18, 18, 18, 8)
        brand_layout.setSpacing(4)

        brand_eyebrow = QLabel("Assistente Locale")
        brand_eyebrow.setObjectName("brand_eyebrow")
        brand_title = QLabel("Vision Desk")
        brand_title.setObjectName("brand_title")
        brand_caption = QLabel("Screenshot, clipboard e analisi visiva in una chat più pulita.")
        brand_caption.setObjectName("brand_caption")
        brand_caption.setWordWrap(True)

        brand_layout.addWidget(brand_eyebrow)
        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(brand_caption)
        self.sidebar_layout.addWidget(brand_block)

        self.btn_new = QPushButton("+ Nuova chat")
        self.btn_new.setObjectName("new_chat_button")
        self.btn_new.clicked.connect(self.new_chat_requested.emit)
        self.sidebar_layout.addWidget(self.btn_new)

        session_label = QLabel("Sessioni recenti")
        session_label.setObjectName("section_label")
        self.sidebar_layout.addWidget(session_label)

        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(lambda item: self.session_selected.emit(item.data(Qt.ItemDataRole.UserRole)))
        self.sidebar_layout.addWidget(self.history_list)

        self.chat_panel = QWidget()
        self.chat_panel.setObjectName("chat_panel")
        chat_layout = QVBoxLayout(self.chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        self.splitter.addWidget(self.chat_panel)
        self.splitter.setSizes([300, 820])

        top_bar = QFrame()
        top_bar.setObjectName("top_bar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(22, 18, 22, 18)
        top_layout.setSpacing(12)

        top_text = QVBoxLayout()
        top_text.setSpacing(2)
        self.chat_title = QLabel("Chat locale")
        self.chat_title.setObjectName("chat_title")
        self.chat_subtitle = QLabel("Traduci, analizza screenshot e continua la conversazione.")
        self.chat_subtitle.setObjectName("chat_subtitle")
        top_text.addWidget(self.chat_title)
        top_text.addWidget(self.chat_subtitle)
        top_layout.addLayout(top_text, 1)

        self.backend_badge = QLabel("Backend: non selezionato")
        self.backend_badge.setObjectName("context_badge")
        self.model_badge = QLabel("Modello: non selezionato")
        self.model_badge.setObjectName("context_badge")
        top_layout.addWidget(self.backend_badge)
        top_layout.addWidget(self.model_badge)
        chat_layout.addWidget(top_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_content = QWidget()
        self.scroll_vbox = QVBoxLayout(self.scroll_content)
        self.scroll_vbox.setContentsMargins(20, 20, 20, 24)
        self.scroll_vbox.setSpacing(14)

        self.empty_state = self.build_welcome_state()
        self.scroll_vbox.addWidget(self.empty_state, 0, Qt.AlignmentFlag.AlignCenter)
        self.scroll_vbox.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        chat_layout.addWidget(self.scroll_area)

        input_container = QWidget()
        input_container.setObjectName("composer")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(18, 14, 18, 16)
        input_layout.setSpacing(8)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")

        composer_card = QFrame()
        composer_card.setObjectName("composer_card")
        composer_layout = QHBoxLayout(composer_card)
        composer_layout.setContentsMargins(10, 8, 8, 8)
        composer_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Scrivi un messaggio, chiedi una traduzione o continua un'analisi...")
        self.input_field.returnPressed.connect(self.send_msg)
        composer_layout.addWidget(self.input_field, 1)

        self.send_button = QPushButton("Invia")
        self.send_button.setObjectName("send_button")
        self.send_button.clicked.connect(self.send_msg)
        composer_layout.addWidget(self.send_button)

        input_layout.addWidget(self.status_label)
        input_layout.addWidget(composer_card)
        chat_layout.addWidget(input_container)

        self.history, self.idx, self.model, self.backend = [], -1, "", ""
        self.scroll_animation = None
        self.update_context_header("", "")

    def build_welcome_state(self):
        card = QFrame()
        card.setObjectName("welcome_card")
        card.setMaximumWidth(760)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        eyebrow = QLabel("Pronto all'analisi")
        eyebrow.setObjectName("welcome_eyebrow")
        title = QLabel("La chat deve accompagnare il motore, non nasconderlo.")
        title.setObjectName("welcome_title")
        title.setWordWrap(True)
        text = QLabel("Questa finestra ora mette in primo piano i punti forti dell'app: cattura schermate, traduzioni rapide e spiegazioni tecniche senza uscire dal desktop.")
        text.setObjectName("welcome_text")
        text.setWordWrap(True)

        feature_shot = QLabel("Screenshot area\nCattura una porzione di schermo e chiedi traduzioni o analisi.")
        feature_shot.setObjectName("welcome_feature")
        feature_clip = QLabel("Clipboard intelligente\nCopia testo da qualsiasi app e trasformalo subito in contesto utile.")
        feature_clip.setObjectName("welcome_feature")
        feature_chat = QLabel("Sessioni persistenti\nRiprendi una conversazione senza perdere modello, backend e storico.")
        feature_chat.setObjectName("welcome_feature")

        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addWidget(feature_shot)
        layout.addWidget(feature_clip)
        layout.addWidget(feature_chat)
        return card

    def update_context_header(self, model, backend):
        current_backend = backend or "non selezionato"
        current_model = model or "non selezionato"
        self.backend_badge.setText(f"Backend: {current_backend}")
        self.model_badge.setText(f"Modello: {current_model}")
        if self.history:
            self.chat_title.setText("Conversazione attiva")
            self.chat_subtitle.setText("Chat persistente per screenshot, testo copiato e follow-up rapidi.")
        else:
            self.chat_title.setText("Chat locale")
            self.chat_subtitle.setText("Traduci, analizza screenshot e continua la conversazione.")

    def toggle_welcome_state(self, visible):
        self.empty_state.setVisible(visible)

    def scroll_to_bottom(self, animated=False, duration=260):
        scrollbar = self.scroll_area.verticalScrollBar()
        target = scrollbar.maximum()
        if animated:
            if self.scroll_animation is not None:
                self.scroll_animation.stop()
            self.scroll_animation = QPropertyAnimation(scrollbar, b"value", self)
            self.scroll_animation.setDuration(duration)
            self.scroll_animation.setStartValue(scrollbar.value())
            self.scroll_animation.setEndValue(target)
            self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.scroll_animation.start()
        else:
            scrollbar.setValue(target)

    def queue_scroll_to_bottom(self, animated=False, duration=260):
        def perform_scroll():
            QApplication.processEvents()
            self.scroll_content.adjustSize()
            self.scroll_area.widget().adjustSize()
            self.scroll_to_bottom(animated=animated, duration=duration)

        QTimer.singleShot(0, perform_scroll)
        QTimer.singleShot(80, perform_scroll)
        QTimer.singleShot(180, perform_scroll)

    def bring_to_front(self):
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

        # Pulse "always on top" briefly to improve focus stealing from tray/screenshot flows on Windows.
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.show()
        self.raise_()
        self.activateWindow()

        def release_topmost():
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.show()
            self.raise_()
            self.activateWindow()

        QTimer.singleShot(180, release_topmost)

    def clear_chat_messages(self):
        # Preserve the welcome card and the final stretch; remove only message bubbles.
        while self.scroll_vbox.count() > 2:
            child = self.scroll_vbox.takeAt(1)
            if child.widget():
                child.widget().deleteLater()

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

        self.clear_chat_messages()
        self.toggle_welcome_state(len(hist) == 0)

        for m in self.history:
            self.add_message_bubble(m['role'], m['content'], m.get('images', []))

        self.update_context_header(model, backend)
        self.bring_to_front()
        if is_new:
            self.ask_ai()

        self.status_label.setText(f"Modello: {model} | Backend: {backend}")

    def add_message_bubble(self, role, content, images=[]):
        self.toggle_welcome_state(False)
        bubble = MessageWidget(role, content, images)
        self.scroll_vbox.insertWidget(self.scroll_vbox.count()-1, bubble, 0, Qt.AlignmentFlag.AlignTop)
        QApplication.processEvents()
        self.queue_scroll_to_bottom(animated=(role == "assistant"), duration=500 if role == "assistant" else 180)

    def send_msg(self):
        txt = self.input_field.text().strip()
        if txt:
            self.history.append({'role': 'user', 'content': txt})
            self.add_message_bubble("user", txt)
            self.input_field.clear()
            self.update_context_header(self.model, self.backend)
            self.ask_ai()
            self.history_updated.emit(self.idx, self.history)

    def ask_ai(self):
        self.status_label.setText(f"Generazione in corso con {self.model}...")
        self.send_button.setEnabled(False)
        self.worker = AIWorker(list(self.history), self.model, self.backend, self.backend_urls)
        self.worker.finished.connect(self.on_res)
        self.worker.start()

    def on_res(self, text, hist):
        self.history = hist
        self.add_message_bubble("assistant", text)
        self.status_label.setText(f"Pronto ({self.model})")
        self.send_button.setEnabled(True)
        self.update_context_header(self.model, self.backend)
        self.history_updated.emit(self.idx, self.history)


class WebChatBridge(QObject):
    send_requested = pyqtSignal(str)
    session_selected = pyqtSignal(int)
    session_delete_requested = pyqtSignal(int)
    new_chat_requested = pyqtSignal()
    ready = pyqtSignal()

    @pyqtSlot(str)
    def submitMessage(self, text):
        self.send_requested.emit(text)

    @pyqtSlot()
    def notifyReady(self):
        self.ready.emit()

    @pyqtSlot(int)
    def openSession(self, index):
        self.session_selected.emit(index)

    @pyqtSlot()
    def createNewChat(self):
        self.new_chat_requested.emit()

    @pyqtSlot(int)
    def deleteSession(self, index):
        self.session_delete_requested.emit(index)


class CodexWebChatWindow(QWidget):
    history_updated = pyqtSignal(int, list)
    session_selected = pyqtSignal(int)
    delete_session_requested = pyqtSignal(int)
    new_chat_requested = pyqtSignal()

    def __init__(self, backend_urls):
        super().__init__()
        self.setWindowTitle("AI Assistant - v3.3")
        self.resize(1180, 780)
        self.setStyleSheet(STYLE_SHEET)
        self.backend_urls = backend_urls
        self.setObjectName("chat_root")
        self.history, self.idx, self.model, self.backend = [], -1, "", ""
        self.is_generating = False
        self.web_ready = False
        self.pending_state = None
        self.sessions_cache = []
        self.current_session_idx = -1
        self.session_factory = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.web_view = QWebEngineView()
        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)
        main_layout.addWidget(self.web_view)

        self.web_channel = QWebChannel(self.web_view.page())
        self.web_bridge = WebChatBridge()
        self.web_channel.registerObject("bridge", self.web_bridge)
        self.web_view.page().setWebChannel(self.web_channel)
        self.web_bridge.send_requested.connect(self.send_msg)
        self.web_bridge.session_selected.connect(self.session_selected.emit)
        self.web_bridge.session_delete_requested.connect(self.delete_session_requested.emit)
        self.web_bridge.new_chat_requested.connect(self.new_chat_requested.emit)
        self.web_bridge.ready.connect(self.on_web_ready)
        self.web_view.loadFinished.connect(self.on_web_load_finished)
        self.web_view.setHtml(self.build_chat_html())

    def build_chat_html(self):
        return """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
  <style>
    :root {
      --panel-border: #232d39;
      --muted: #8c9bad;
      --text: #e8eef5;
      --text-soft: #cad5e2;
      --assistant-line: #232c38;
      --user-line: #355c8e;
      --code-bg: #0d1218;
      --composer-border: #273241;
      --button: #3f86e8;
      --button-hover: #5797ef;
      --sidebar-bg: rgba(13, 18, 24, 0.94);
      --sidebar-border: #1f2935;
      --card-bg: rgba(18, 24, 31, 0.84);
      --card-border: #283544;
      --active-session: #172332;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      height: 100%;
      background:
        radial-gradient(circle at top left, rgba(67, 104, 154, 0.20), transparent 28%),
        radial-gradient(circle at 80% 20%, rgba(51, 86, 124, 0.15), transparent 24%),
        linear-gradient(180deg, #12171d 0%, #0f141a 100%);
      color: var(--text);
      font-family: "Segoe UI Variable", "Segoe UI", sans-serif;
      overflow: hidden;
    }
    .app-shell {
      height: 100%;
      min-height: 0;
      display: grid;
      grid-template-columns: var(--sidebar-width, 312px) 10px minmax(0, 1fr);
    }
    .sidebar {
      display: flex;
      flex-direction: column;
      min-width: 0;
      min-height: 0;
      background: var(--sidebar-bg);
      border-right: 1px solid var(--sidebar-border);
      backdrop-filter: blur(18px);
    }
    .divider {
      position: relative;
      cursor: col-resize;
      background: linear-gradient(180deg, rgba(27, 36, 46, 0.95) 0%, rgba(17, 23, 31, 0.95) 100%);
      border-left: 1px solid rgba(53, 71, 90, 0.45);
      border-right: 1px solid rgba(14, 19, 25, 0.75);
    }
    .divider::after {
      content: "";
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 4px;
      height: 52px;
      border-radius: 999px;
      background: linear-gradient(180deg, #60758d 0%, #3d4c5d 100%);
      box-shadow: 0 0 0 1px rgba(10, 14, 20, 0.35);
    }
    .divider:hover::after,
    .divider.dragging::after {
      background: linear-gradient(180deg, #7f9fc0 0%, #56718f 100%);
    }
    .sidebar-header {
      padding: 18px 18px 14px 18px;
      border-bottom: 1px solid rgba(38, 51, 66, 0.62);
    }
    .brand-kicker {
      color: #89a1b8;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.05px;
      text-transform: uppercase;
      margin-bottom: 6px;
    }
    .brand-title {
      color: #f5f8fb;
      font-size: 26px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .brand-copy {
      color: #8c9bad;
      font-size: 12px;
      line-height: 1.5;
    }
    .new-chat-button {
      margin: 16px 18px 10px 18px;
      width: calc(100% - 36px);
      padding: 13px 16px;
      border-radius: 16px;
      border: 1px solid #395272;
      background: linear-gradient(180deg, #eaf2fb 0%, #d7e5f7 100%);
      color: #0f1a24;
      font-weight: 800;
      font-size: 13px;
    }
    .new-chat-button:hover {
      background: linear-gradient(180deg, #f5f9fd 0%, #dfeaf9 100%);
    }
    .sidebar-section {
      padding: 8px 18px 10px 18px;
      color: #6f8398;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
    }
    .session-list {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      padding: 0 12px 14px 12px;
    }
    .session-list::-webkit-scrollbar { width: 12px; }
    .session-list::-webkit-scrollbar-track {
      background: rgba(10, 14, 20, 0.26);
      border-left: 1px solid rgba(42, 54, 67, 0.22);
    }
    .session-list::-webkit-scrollbar-thumb {
      background: #445569;
      border-radius: 999px;
      border: 2px solid rgba(10, 14, 20, 0.18);
    }
    .session-list::-webkit-scrollbar-thumb:hover {
      background: #5a6f88;
    }
    .session-item {
      width: 100%;
      border: 1px solid transparent;
      background: transparent;
      color: #dbe6f1;
      text-align: left;
      border-radius: 14px;
      padding: 9px 10px 9px 12px;
      margin-bottom: 6px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: background 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
    }
    .session-row {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      width: 100%;
    }
    .session-copy {
      flex: 1;
      min-width: 0;
    }
    .session-item:hover {
      background: rgba(24, 34, 46, 0.8);
      border-color: #293647;
    }
    .session-item.active {
      background: linear-gradient(180deg, rgba(25, 39, 56, 0.96) 0%, rgba(20, 32, 46, 0.96) 100%);
      border-color: #4e78a4;
      box-shadow: inset 0 0 0 1px rgba(138, 187, 245, 0.14), 0 0 0 1px rgba(8, 12, 16, 0.16);
    }
    .session-title {
      font-size: 12px;
      font-weight: 700;
      color: #eef4fb;
      line-height: 1.25;
    }
    .session-meta {
      font-size: 10px;
      color: #8ca0b5;
      line-height: 1.2;
    }
    .session-delete {
      flex: 0 0 auto;
      min-width: 24px;
      width: 24px;
      height: 24px;
      padding: 0;
      border-radius: 8px;
      background: rgba(36, 47, 60, 0.86);
      color: #94a7bc;
      font-size: 13px;
      line-height: 1;
    }
    .session-delete:hover {
      background: rgba(98, 44, 44, 0.92);
      color: #fff0f0;
    }
    .content-shell {
      min-width: 0;
      min-height: 0;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 20px 24px 16px 24px;
      border-bottom: 1px solid var(--panel-border);
      background: rgba(16, 21, 27, 0.72);
      backdrop-filter: blur(14px);
    }
    .topbar-copy { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
    .eyebrow { color: #7f92a7; font-size: 11px; font-weight: 700; letter-spacing: 1.1px; text-transform: uppercase; }
    .title { color: #f5f8fb; font-size: 24px; font-weight: 700; }
    .subtitle { color: var(--muted); font-size: 12px; }
    .topbar-meta { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
    .badge {
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid #304154;
      background: rgba(30, 41, 54, 0.88);
      color: #dfe7f0;
      font-size: 11px;
      font-weight: 700;
    }
    .messages {
      min-height: 0;
      overflow-y: auto;
      scroll-behavior: smooth;
      padding: 20px 28px 26px 28px;
    }
    .messages::-webkit-scrollbar { width: 12px; }
    .messages::-webkit-scrollbar-track {
      background: rgba(10, 14, 20, 0.20);
      border-left: 1px solid rgba(42, 54, 67, 0.16);
    }
    .messages::-webkit-scrollbar-thumb {
      background: #48596d;
      border-radius: 999px;
      border: 2px solid rgba(10, 14, 20, 0.18);
    }
    .messages::-webkit-scrollbar-thumb:hover {
      background: #61778f;
    }
    .welcome {
      max-width: 860px;
      margin: 32px auto 24px auto;
      padding: 28px 30px;
      border: 1px solid #263241;
      border-radius: 26px;
      background: rgba(16, 21, 28, 0.86);
      box-shadow: 0 20px 70px rgba(0, 0, 0, 0.18);
    }
    .welcome h1 { margin: 8px 0 10px 0; font-size: 30px; line-height: 1.15; color: #f5f8fb; }
    .welcome p { margin: 0 0 18px 0; color: #a8b8c8; font-size: 14px; line-height: 1.6; max-width: 720px; }
    .welcome-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
    .welcome-card {
      border: 1px solid #273445;
      border-radius: 18px;
      background: rgba(11, 16, 23, 0.75);
      padding: 14px 15px;
      color: #d7e1ed;
      line-height: 1.5;
      font-size: 13px;
    }
    .message { max-width: 860px; margin: 0 auto 24px auto; }
    .message-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.9px;
      text-transform: uppercase;
    }
    .message-line { height: 1px; flex: 1; min-width: 24px; background: var(--assistant-line); }
    .message.user .message-line { background: var(--user-line); }
    .message-body { color: var(--text-soft); font-size: 15px; line-height: 1.68; overflow-wrap: anywhere; }
    .message.user .message-body { color: #eef4fb; }
    .message-body p { margin: 0 0 14px 0; }
    .message-body p:last-child { margin-bottom: 0; }
    .message-body pre {
      margin: 14px 0;
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid #263241;
      background: var(--code-bg);
      color: #e8eef5;
      overflow-x: auto;
      white-space: pre-wrap;
    }
    .message-body code {
      padding: 2px 5px;
      border-radius: 5px;
      background: #202a36;
      color: #9cccff;
      font-family: Consolas, monospace;
      font-size: 0.95em;
    }
    .message-body pre code { padding: 0; background: transparent; color: inherit; }
    .message-image {
      display: block;
      max-width: min(100%, 560px);
      margin: 0 0 14px 0;
      border-radius: 16px;
      border: 1px solid #2b3644;
    }
    .composer-shell {
      flex-shrink: 0;
      border-top: 1px solid var(--panel-border);
      padding: 16px 22px 20px 22px;
      background: rgba(16, 21, 27, 0.84);
      backdrop-filter: blur(14px);
    }
    .status { min-height: 16px; margin: 0 auto 8px auto; max-width: 860px; color: #8294a8; font-size: 11px; }
    .composer-card {
      max-width: 860px;
      margin: 0 auto;
      border-radius: 22px;
      border: 1px solid var(--composer-border);
      background: linear-gradient(180deg, rgba(26, 33, 43, 0.98) 0%, rgba(20, 27, 36, 0.98) 100%);
      overflow: hidden;
    }
    .composer-form { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 10px; padding: 12px 12px 12px 14px; }
    textarea {
      resize: none;
      min-height: 72px;
      max-height: 200px;
      border: none;
      outline: none;
      background: transparent;
      color: #eff5fb;
      font: inherit;
      font-size: 15px;
      line-height: 1.5;
    }
    textarea::placeholder { color: #708196; }
    button {
      border: none;
      outline: none;
      cursor: pointer;
      padding: 12px 16px;
      border-radius: 16px;
      background: var(--button);
      color: #ffffff;
      font: inherit;
      font-size: 13px;
      font-weight: 700;
      min-width: 92px;
    }
    button:hover { background: var(--button-hover); }
    button:disabled { background: #2b3a4a; color: #91a2b5; cursor: default; }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="brand-kicker">Assistente locale</div>
        <div class="brand-title">AI Assistant</div>
        <div class="brand-copy">Una shell desktop più coerente, con cronologia e conversazione nello stesso linguaggio visivo.</div>
      </div>
      <button class="new-chat-button" id="new-chat-button" type="button">+ Nuova chat</button>
      <div class="sidebar-section">Sessioni recenti</div>
      <div class="session-list" id="session-list"></div>
    </aside>
    <div class="divider" id="sidebar-divider" title="Trascina per ridimensionare"></div>
    <div class="content-shell">
      <header class="topbar">
        <div class="topbar-copy">
          <div class="eyebrow">Workspace locale</div>
          <div class="title" id="chat-title">Chat locale</div>
          <div class="subtitle" id="chat-subtitle">Traduci, analizza screenshot e continua la conversazione.</div>
        </div>
        <div class="topbar-meta">
          <div class="badge" id="badge-backend">Backend: non selezionato</div>
          <div class="badge" id="badge-model">Modello: non selezionato</div>
        </div>
      </header>
      <main class="messages" id="messages"></main>
      <footer class="composer-shell">
        <div class="status" id="status-line"></div>
        <div class="composer-card">
          <form class="composer-form" id="composer-form">
            <textarea id="composer-input" placeholder="Scrivi un messaggio, chiedi una traduzione o continua un'analisi..."></textarea>
            <button type="submit" id="composer-send">Invia</button>
          </form>
        </div>
      </footer>
    </div>
  </div>
  <script>
    let bridge = null;
    let latestState = null;
    let isDraggingDivider = false;
    function setSidebarWidth(width) {
      const clamped = Math.max(260, Math.min(520, width));
      document.documentElement.style.setProperty("--sidebar-width", clamped + "px");
    }
    function scrollMessages(animated = true) {
      const messages = document.getElementById("messages");
      messages.scrollTo({ top: messages.scrollHeight, behavior: animated ? "smooth" : "auto" });
    }
    function escapeHtml(value) {
      return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
    }
    function setBusy(isBusy) {
      const input = document.getElementById("composer-input");
      const button = document.getElementById("composer-send");
      input.disabled = !!isBusy;
      button.disabled = !!isBusy || !input.value.trim();
    }
    function updateSendEnabled() {
      const input = document.getElementById("composer-input");
      const button = document.getElementById("composer-send");
      button.disabled = !!(latestState && latestState.busy) || !input.value.trim();
    }
    function renderSessions(state) {
      const list = document.getElementById("session-list");
      list.innerHTML = "";
      state.sessions.forEach((session) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "session-item" + (session.selected ? " active" : "");
        item.innerHTML = `
          <div class="session-row">
            <div class="session-copy">
              <div class="session-title">${escapeHtml(session.label)}</div>
              <div class="session-meta">${escapeHtml(session.meta)}</div>
            </div>
            <button type="button" class="session-delete" title="Elimina chat">×</button>
          </div>`;
        item.querySelector(".session-delete").addEventListener("click", (event) => {
          event.stopPropagation();
          const confirmed = window.confirm(`Eliminare la chat "${session.label}"?`);
          if (confirmed && bridge) bridge.deleteSession(session.index);
        });
        item.addEventListener("click", () => {
          if (bridge) bridge.openSession(session.index);
        });
        list.appendChild(item);
      });
    }
    function renderState(state) {
      latestState = state;
      document.getElementById("chat-title").textContent = state.title;
      document.getElementById("chat-subtitle").textContent = state.subtitle;
      document.getElementById("badge-backend").textContent = "Backend: " + state.backend;
      document.getElementById("badge-model").textContent = "Modello: " + state.model;
      document.getElementById("status-line").textContent = state.status;
      renderSessions(state);
      const messages = document.getElementById("messages");
      messages.innerHTML = "";
      if (state.showWelcome) {
        const welcome = document.createElement("section");
        welcome.className = "welcome";
        welcome.innerHTML = `
          <div class="eyebrow">Pronto all'analisi</div>
          <h1>Una chat desktop sobria, veloce e focalizzata sul lavoro.</h1>
          <p>Screenshot, clipboard e follow-up convivono in una UI più vicina a Codex: meno bolle, più testo, più spazio e una gerarchia visiva pulita.</p>
          <div class="welcome-grid">
            <div class="welcome-card">Screenshot area<br>Cattura una porzione di schermo e chiedi traduzioni o analisi.</div>
            <div class="welcome-card">Clipboard intelligente<br>Prendi testo da qualsiasi app e trasformalo in contesto utile.</div>
            <div class="welcome-card">Sessioni persistenti<br>Riprendi il filo senza perdere modello, backend o immagini.</div>
          </div>`;
        messages.appendChild(welcome);
      }
      state.messages.forEach((message) => {
        const wrapper = document.createElement("article");
        wrapper.className = "message " + message.role;
        const meta = document.createElement("div");
        meta.className = "message-meta";
        meta.innerHTML = `<span>${escapeHtml(message.label)}</span><div class="message-line"></div>`;
        wrapper.appendChild(meta);
        if (message.images && message.images.length) {
          message.images.forEach((src) => {
            const img = document.createElement("img");
            img.className = "message-image";
            img.src = src;
            img.addEventListener("load", () => {
              if (state.forceScroll) scrollMessages(false);
            });
            wrapper.appendChild(img);
          });
        }
        const body = document.createElement("div");
        body.className = "message-body";
        body.innerHTML = message.html;
        wrapper.appendChild(body);
        messages.appendChild(wrapper);
      });
      setBusy(state.busy);
      if (state.forceScroll) {
        requestAnimationFrame(() => scrollMessages(true));
        setTimeout(() => scrollMessages(true), 120);
        setTimeout(() => scrollMessages(false), 260);
        setTimeout(() => scrollMessages(false), 600);
      }
    }
    document.addEventListener("DOMContentLoaded", () => {
      const form = document.getElementById("composer-form");
      const input = document.getElementById("composer-input");
      const divider = document.getElementById("sidebar-divider");
      document.getElementById("new-chat-button").addEventListener("click", () => {
        if (bridge) bridge.createNewChat();
      });
      divider.addEventListener("mousedown", () => {
        isDraggingDivider = true;
        divider.classList.add("dragging");
        document.body.style.userSelect = "none";
      });
      window.addEventListener("mousemove", (event) => {
        if (!isDraggingDivider) return;
        setSidebarWidth(event.clientX);
      });
      window.addEventListener("mouseup", () => {
        if (!isDraggingDivider) return;
        isDraggingDivider = false;
        divider.classList.remove("dragging");
        document.body.style.userSelect = "";
      });
      input.addEventListener("input", updateSendEnabled);
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          form.requestSubmit();
        }
      });
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        const value = input.value.trim();
        if (!value || !bridge || (latestState && latestState.busy)) return;
        bridge.submitMessage(value);
        input.value = "";
        updateSendEnabled();
      });
      if (typeof QWebChannel !== "undefined") {
        new QWebChannel(qt.webChannelTransport, function(channel) {
          bridge = channel.objects.bridge;
          bridge.notifyReady();
        });
      }
      updateSendEnabled();
    });
  </script>
</body>
</html>"""

    def on_web_load_finished(self, ok):
        self.web_ready = ok
        if ok and self.pending_state:
            self.render_web_state()

    def on_web_ready(self):
        self.web_ready = True
        self.render_web_state()

    def message_to_html(self, content):
        return markdown.markdown(content, extensions=["fenced_code", "tables", "nl2br", "sane_lists"], output_format="html5")

    def build_web_state(self, force_scroll=False):
        messages = []
        for item in self.history:
            image_urls = []
            for image in item.get("images", []):
                image_bytes = base64.b64decode(image) if isinstance(image, str) else image
                image_urls.append(f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}")
            messages.append({
                "role": item["role"],
                "label": "Tu" if item["role"] == "user" else "Assistente locale",
                "html": self.message_to_html(item["content"]),
                "images": image_urls,
            })

        title = "Conversazione attiva" if self.history else "Chat locale"
        subtitle = "Interfaccia in webview per una chat più vicina a un'app desktop moderna." if self.history else "Traduci, analizza screenshot e continua la conversazione."
        status = f"Generazione in corso con {self.model or 'il modello selezionato'}..." if self.is_generating else (f"Pronto ({self.model})" if self.model else "Pronto")
        sessions = []
        for index, session in enumerate(self.sessions_cache):
            real_index = index
            label = session.get("label", f"Sess {real_index+1}")
            meta_parts = []
            if session.get("backend"):
                meta_parts.append(session["backend"])
            if session.get("model"):
                meta_parts.append(session["model"])
            meta = " • ".join(meta_parts) if meta_parts else "Sessione salvata"
            sessions.append({
                "index": real_index,
                "label": label,
                "meta": meta,
                "selected": real_index == self.current_session_idx,
            })
        return {
            "title": title,
            "subtitle": subtitle,
            "backend": self.backend or "non selezionato",
            "model": self.model or "non selezionato",
            "status": status,
            "busy": self.is_generating,
            "showWelcome": len(self.history) == 0,
            "sessions": sessions,
            "messages": messages,
            "forceScroll": force_scroll,
        }

    def render_web_state(self, force_scroll=False):
        state = self.build_web_state(force_scroll=force_scroll)
        self.pending_state = state
        if not self.web_ready:
            return
        self.web_view.page().runJavaScript(f"renderState({json.dumps(state, ensure_ascii=False)});")

    def bring_to_front(self):
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.show()
        self.raise_()
        self.activateWindow()

        def release_topmost():
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.show()
            self.raise_()
            self.activateWindow()

        QTimer.singleShot(180, release_topmost)

    def update_sidebar(self, sessions, current_idx=-1):
        self.sessions_cache = list(sessions)
        self.current_session_idx = current_idx
        self.render_web_state()

    def load_session(self, idx, hist, model, backend, is_new=False, bring_forward=False):
        self.idx, self.history, self.model, self.backend = idx, hist, model, backend
        self.current_session_idx = idx
        self.render_web_state(force_scroll=True)
        if bring_forward:
            self.bring_to_front()
        if is_new:
            self.ask_ai()

    def send_msg(self, text=None):
        txt = (text or "").strip()
        if not txt or self.is_generating:
            return
        if self.idx < 0:
            if callable(self.session_factory):
                self.session_factory()
            else:
                self.new_chat_requested.emit()
            if self.idx < 0:
                return
        self.history.append({'role': 'user', 'content': txt})
        self.render_web_state(force_scroll=True)
        self.ask_ai()
        self.history_updated.emit(self.idx, self.history)

    def ask_ai(self):
        self.is_generating = True
        self.render_web_state()
        self.worker = AIWorker(list(self.history), self.model, self.backend, self.backend_urls)
        self.worker.finished.connect(self.on_res)
        self.worker.start()

    def on_res(self, text, hist):
        self.history = hist
        self.is_generating = False
        self.render_web_state(force_scroll=True)
        self.history_updated.emit(self.idx, self.history)


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.active_backend = AIBackend.OLLAMA
        self.active_model = ""
        self.sessions = []
        self.native_snip_timer = None
        self.native_snip_deadline = 0
        self.native_snip_last_hash = None
        
        # Load configuration
        self.backend_urls = self.load_config()
        
        # Initialize SQLite database for history
        self.init_db()
        self.load_history_from_db()
        
        self.chat_window = CodexWebChatWindow(self.backend_urls)
        self.chat_window.session_factory = self.start_new_session_ui
        self.chat_window.history_updated.connect(self.save_updated_history)
        self.chat_window.session_selected.connect(self.restore)
        self.chat_window.delete_session_requested.connect(self.delete_session)
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

    def load_history_from_disk(self):
        # This method is now deprecated since we're using the database
        # Keeping it for backward compatibility but it won't be called anymore
        pass

    def start_new_session_ui(self):
        idx = len(self.sessions)
        label = f"Nuova chat ({datetime.now().strftime('%d/%m %H:%M')})"
        session = {
            'label': label,
            'history': [],
            'model': self.active_model,
            'backend': self.active_backend,
            'id': None,
        }
        self.sessions.append(session)
        self.chat_window.update_sidebar(self.sessions, idx)
        self.chat_window.load_session(idx, session['history'], self.active_model, self.active_backend, is_new=False, bring_forward=True)
        return idx

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

    def init_db(self):
        """Initialize the SQLite database for chat history"""
        try:
            conn = sqlite3.connect('chat_history.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    model TEXT,
                    backend TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    images TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing database: {e}")

    def load_history_from_db(self):
        """Load chat history from SQLite database"""
        try:
            conn = sqlite3.connect('chat_history.db')
            cursor = conn.cursor()
            # Load only non-deleted sessions
            cursor.execute('''
                SELECT id, label, model, backend, created_at, updated_at
                FROM sessions 
                WHERE is_deleted = 0
                ORDER BY updated_at DESC, created_at DESC, id DESC
            ''')
            sessions_data = cursor.fetchall()
            
            for session_data in sessions_data:
                session_id, label, model, backend, created_at, updated_at = session_data
                # Load messages for this session
                cursor.execute('''
                    SELECT role, content, images
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY created_at ASC
                ''', (session_id,))
                messages_data = cursor.fetchall()
                
                # Convert messages to proper format
                history = []
                for role, content, images in messages_data:
                    message = {'role': role, 'content': content}
                    if images:
                        # Decode base64 images if they exist
                        try:
                            image_list = json.loads(images)
                            message['images'] = [base64.b64decode(img) for img in image_list]
                        except:
                            pass
                    history.append(message)
                
                # Add to sessions list
                self.sessions.append({
                    'id': session_id,
                    'label': label,
                    'model': model,
                    'backend': backend,
                    'history': history,
                    'created_at': created_at,
                    'updated_at': updated_at
                })
            
            conn.close()
        except Exception as e:
            print(f"Error loading history from database: {e}")

    def sort_sessions(self, current_session=None):
        def sort_key(session):
            return (
                session.get('updated_at') or "",
                session.get('created_at') or "",
                session.get('id') or 0,
            )

        self.sessions.sort(key=sort_key, reverse=True)
        if current_session is None:
            return -1
        try:
            return self.sessions.index(current_session)
        except ValueError:
            return -1

    def save_updated_history(self, i, h):
        if i < 0 or i >= len(self.sessions):
            return -1

        self.sessions[i]['history'] = h
        self.sessions[i]['model'] = self.active_model
        self.sessions[i]['backend'] = self.active_backend

        if h:
            first_user_message = next((msg.get('content', '').strip() for msg in h if msg.get('role') == 'user' and msg.get('content')), "")
            if first_user_message:
                base_label = first_user_message[:30] + "..." if len(first_user_message) > 30 else first_user_message
                current_label = self.sessions[i].get('label', '')
                if current_label.startswith("Nuova chat (") or current_label.startswith("Ciao! Come posso aiutarti oggi?"):
                    timestamp = datetime.now().strftime('%d/%m %H:%M')
                    self.sessions[i]['label'] = f"{base_label} ({timestamp})"

        # Update the session in database instead of JSON file
        try:
            conn = sqlite3.connect('chat_history.db')
            cursor = conn.cursor()
            
            # Check if session already has an ID (i.e., it was loaded from database)
            if 'id' in self.sessions[i] and self.sessions[i]['id'] is not None:
                session_id = self.sessions[i]['id']
                # Update existing session
                cursor.execute('''
                    UPDATE sessions 
                    SET label = ?, model = ?, backend = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (self.sessions[i]['label'], self.active_model, self.active_backend, session_id))
            else:
                # For new sessions, we need to create a new session entry and get the ID
                cursor.execute('''
                    INSERT INTO sessions (label, model, backend)
                    VALUES (?, ?, ?)
                ''', (self.sessions[i]['label'], self.active_model, self.active_backend))
                session_id = cursor.lastrowid
                # Store the ID in our session data for future updates
                self.sessions[i]['id'] = session_id
            
            # Delete existing messages for this session
            cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            
            # Insert new messages
            for msg in h:
                images = None
                if 'images' in msg and msg['images']:
                    try:
                        image_list = [base64.b64encode(img).decode('utf-8') if isinstance(img, bytes) else img for img in msg['images']]
                        images = json.dumps(image_list)
                    except:
                        pass
                cursor.execute('''
                    INSERT INTO messages (session_id, role, content, images)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, msg['role'], msg['content'], images))
            
            conn.commit()
            conn.close()
            now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            if 'created_at' not in self.sessions[i] or not self.sessions[i]['created_at']:
                self.sessions[i]['created_at'] = now_str
            self.sessions[i]['updated_at'] = now_str

            current_session = self.sessions[i]
            new_index = self.sort_sessions(current_session)
            self.chat_window.idx = new_index
            self.chat_window.update_sidebar(self.sessions, new_index)
            return new_index
        except Exception as e:
            print(f"Error saving history to database: {e}")
            return i

    def clear_history_db(self):
        """Clear all history from the database"""
        try:
            conn = sqlite3.connect('chat_history.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE sessions SET is_deleted = 1')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error clearing database: {e}")

    def delete_session(self, idx):
        if idx < 0 or idx >= len(self.sessions):
            return

        session = self.sessions[idx]
        try:
            conn = sqlite3.connect('chat_history.db')
            cursor = conn.cursor()
            if session.get('id') is not None:
                cursor.execute('UPDATE sessions SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (session['id'],))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error deleting session from database: {e}")

        del self.sessions[idx]

        if not self.sessions:
            self.chat_window.update_sidebar([], -1)
            self.chat_window.load_session(-1, [], self.active_model, self.active_backend, is_new=False, bring_forward=False)
            return

        new_idx = min(idx, len(self.sessions) - 1)
        self.chat_window.update_sidebar(self.sessions, new_idx)
        target = self.sessions[new_idx]
        self.chat_window.load_session(new_idx, target['history'], target['model'], target['backend'], is_new=False, bring_forward=False)


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
            # Clear database
            self.clear_history_db()
            if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)

    def set_bk(self, b): self.active_backend = b; self.refresh_mods(); self.update_menu()
    def set_mod(self, x): self.active_model = x; self.update_menu()
    def start_vision(self):
        self.tray.contextMenu().hide()
        QApplication.processEvents()
        time.sleep(0.15)
        self.start_native_screen_snip()

    def start_native_screen_snip(self):
        self.native_snip_last_hash = self.get_clipboard_image_hash()
        self.native_snip_deadline = time.time() + 20
        if self.native_snip_timer is None:
            self.native_snip_timer = QTimer()
            self.native_snip_timer.setInterval(250)
            self.native_snip_timer.timeout.connect(self.poll_native_screen_snip)
        self.native_snip_timer.start()
        try:
            os.startfile("ms-screenclip:")
        except OSError:
            self.native_snip_timer.stop()
            self.snipper = SnippingTool(self.process)

    def get_clipboard_image_hash(self):
        try:
            clip = ImageGrab.grabclipboard()
            if isinstance(clip, Image.Image):
                img = clip.convert("RGB")
                return hash(img.tobytes())
        except Exception:
            pass
        return None

    def poll_native_screen_snip(self):
        if time.time() > self.native_snip_deadline:
            self.native_snip_timer.stop()
            return

        try:
            clip = ImageGrab.grabclipboard()
        except Exception:
            return

        if not isinstance(clip, Image.Image):
            return

        image = clip.convert("RGB")
        current_hash = hash(image.tobytes())
        if current_hash == self.native_snip_last_hash:
            return

        self.native_snip_timer.stop()
        self.native_snip_last_hash = current_hash
        self.process(image_to_png_bytes(image), False)

    def start_text_grab(self):
        self.tray.contextMenu().hide(); QApplication.processEvents(); time.sleep(0.4)
        pyautogui.hotkey('ctrl', 'c'); time.sleep(0.3)
        txt = pyperclip.paste()
        if txt.strip(): self.process(f"Analizza e spiega questo testo in italiano:\n\n{txt}", True)

    def process(self, data, is_txt):
        idx = len(self.sessions)
        if is_txt: 
            hist = [{'role': 'user', 'content': data}]
            # Generate a label based on the first user message content
            label = data[:30] + "..." if len(data) > 30 else data
        else:
            p = "Analizza questa immagine. Se vedi testo, traducilo in italiano. Spiega errori o codice. Rispondi in italiano."
            hist = [{'role': 'user', 'content': p, 'images': [data]}]
            label = "Analisi Immagine"
        self.sessions.append({'label': f"{label} ({datetime.now().strftime('%d/%m %H:%M')})", 'history': hist, 'model': self.active_model, 'backend': self.active_backend})
        new_idx = self.save_updated_history(idx, hist)
        if new_idx < 0:
            new_idx = idx
        self.chat_window.update_sidebar(self.sessions, new_idx)
        self.chat_window.load_session(new_idx, hist, self.active_model, self.active_backend, is_new=True, bring_forward=True)

    def restore(self, i):
        s = self.sessions[i]
        self.chat_window.load_session(i, s['history'], s['model'], s['backend'], bring_forward=False)

    def run(self): sys.exit(self.app.exec())

if __name__ == "__main__":
    MainApp().run()
