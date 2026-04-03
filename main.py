import sys
import os
import base64
import requests
import json
import re
import markdown
from datetime import datetime

from controllers.tray_controller import TrayController
from core.config import (
    APP_DATA_DIR,
    CHAT_DB_FILE,
    CONFIG_FILE,
    HISTORY_FILE,
    load_runtime_config,
    save_runtime_config,
)
from core.i18n import APP_NAME, APP_VERSION, tr
from services.session_service import (
    clear_history_db,
    delete_session as delete_stored_session,
    init_db,
    load_legacy_history,
    load_sessions_from_db,
    persist_session_update,
    rename_session as rename_stored_session,
)
from ui.about_dialog import AboutDialog
from ui.config_dialog import ConfigDialog
from workers.ai_worker import AIWorker

# --- CONFIGURAZIONE SISTEMA ---
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
                             QLineEdit, QPushButton, QLabel, QSystemTrayIcon, 
                             QStyle, QMessageBox, QListWidget, QListWidgetItem, 
                             QScrollArea, QFrame, QSizePolicy, QAbstractItemView, QDialog, 
                             QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QObject, QSize, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

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
    OPENAI_COMPATIBLE = "Compatibile OpenAI"

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
    def __init__(self, role, content, images=None, language="it"):
        super().__init__()
        self.role = role
        self.language = language
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 8, 28, 8)

        if role == 'user':
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            text_color = "#dfe8f2"
            meta_color = "#7fb0ff"
            label_text = tr("you", self.language)
            accent = "#2f6fca"
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            text_color = "#edf3f9"
            meta_color = "#91a3b5"
            label_text = tr("assistant_local", self.language)
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

class OllamaChatWindow(QWidget):
    history_updated = pyqtSignal(int, list)
    session_selected = pyqtSignal(int)
    new_chat_requested = pyqtSignal()

    def __init__(self, backend_urls, language="it"):
        super().__init__()
        self.language = language
        self.setWindowTitle(tr("window_title", self.language))
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

        brand_eyebrow = QLabel(tr("assistant_local_caps", self.language))
        brand_eyebrow.setObjectName("brand_eyebrow")
        brand_title = QLabel(tr("app_title", self.language))
        brand_title.setObjectName("brand_title")
        brand_caption = QLabel(tr("legacy_brand_caption", self.language))
        brand_caption.setObjectName("brand_caption")
        brand_caption.setWordWrap(True)

        brand_layout.addWidget(brand_eyebrow)
        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(brand_caption)
        self.sidebar_layout.addWidget(brand_block)

        self.btn_new = QPushButton(tr("new_chat", self.language))
        self.btn_new.setObjectName("new_chat_button")
        self.btn_new.clicked.connect(self.new_chat_requested.emit)
        self.sidebar_layout.addWidget(self.btn_new)

        session_label = QLabel(tr("recent_sessions", self.language))
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
        self.chat_title = QLabel(tr("chat_local", self.language))
        self.chat_title.setObjectName("chat_title")
        self.chat_subtitle = QLabel(tr("chat_subtitle", self.language))
        self.chat_subtitle.setObjectName("chat_subtitle")
        top_text.addWidget(self.chat_title)
        top_text.addWidget(self.chat_subtitle)
        top_layout.addLayout(top_text, 1)

        self.backend_badge = QLabel(tr("backend_badge", self.language, value=tr("not_selected", self.language)))
        self.backend_badge.setObjectName("context_badge")
        self.model_badge = QLabel(tr("model_badge", self.language, value=tr("not_selected", self.language)))
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
        self.input_field.setPlaceholderText(tr("input_placeholder", self.language))
        self.input_field.returnPressed.connect(self.send_msg)
        composer_layout.addWidget(self.input_field, 1)

        self.send_button = QPushButton(tr("send", self.language))
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

        eyebrow = QLabel(tr("ready_analysis", self.language))
        eyebrow.setObjectName("welcome_eyebrow")
        title = QLabel(tr("welcome_title", self.language))
        title.setObjectName("welcome_title")
        title.setWordWrap(True)
        text = QLabel(tr("welcome_text", self.language))
        text.setObjectName("welcome_text")
        text.setWordWrap(True)

        feature_shot = QLabel(tr("welcome_feature_shot", self.language))
        feature_shot.setObjectName("welcome_feature")
        feature_clip = QLabel(tr("welcome_feature_clip", self.language))
        feature_clip.setObjectName("welcome_feature")
        feature_chat = QLabel(tr("welcome_feature_chat", self.language))
        feature_chat.setObjectName("welcome_feature")

        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addWidget(feature_shot)
        layout.addWidget(feature_clip)
        layout.addWidget(feature_chat)
        return card

    def update_context_header(self, model, backend):
        current_backend = backend or tr("not_selected", self.language)
        current_model = model or tr("not_selected", self.language)
        self.backend_badge.setText(tr("backend_badge", self.language, value=current_backend))
        self.model_badge.setText(tr("model_badge", self.language, value=current_model))
        if self.history:
            self.chat_title.setText(tr("active_conversation", self.language))
            self.chat_subtitle.setText(tr("chat_subtitle_active", self.language))
        else:
            self.chat_title.setText(tr("chat_local", self.language))
            self.chat_subtitle.setText(tr("chat_subtitle", self.language))

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
            item = QListWidgetItem(s.get('label', tr("session_fallback", self.language, index=real_idx + 1)))
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

        self.status_label.setText(tr("status_model_backend", self.language, model=model, backend=backend))

    def add_message_bubble(self, role, content, images=[]):
        self.toggle_welcome_state(False)
        bubble = MessageWidget(role, content, images, self.language)
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
        self.status_label.setText(tr("status_generating", self.language, model=self.model))
        self.send_button.setEnabled(False)
        self.worker = AIWorker(list(self.history), self.model, self.backend, self.backend_urls, AIBackend.OLLAMA, self.language)
        self.worker.finished.connect(self.on_res)
        self.worker.start()

    def on_res(self, text, hist):
        self.history = hist
        self.add_message_bubble("assistant", text)
        self.status_label.setText(tr("status_ready_model", self.language, model=self.model))
        self.send_button.setEnabled(True)
        self.update_context_header(self.model, self.backend)
        self.history_updated.emit(self.idx, self.history)


class WebChatBridge(QObject):
    send_requested = pyqtSignal(str)
    session_selected = pyqtSignal(int)
    session_delete_requested = pyqtSignal(int)
    session_rename_requested = pyqtSignal(int, str)
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

    @pyqtSlot(int, str)
    def renameSession(self, index, label):
        self.session_rename_requested.emit(index, label)


class CodexWebChatWindow(QWidget):
    history_updated = pyqtSignal(int, list)
    session_selected = pyqtSignal(int)
    delete_session_requested = pyqtSignal(int)
    rename_session_requested = pyqtSignal(int, str)
    new_chat_requested = pyqtSignal()

    def __init__(self, backend_urls, language="it"):
        super().__init__()
        self.language = language
        self.setWindowTitle(tr("window_title", self.language))
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
        self.active_workers = []

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.web_view = QWebEngineView()
        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.web_view.setStyleSheet("background-color: #15191f; border: none;")
        self.web_view.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.web_view.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)
        self.web_view.page().setBackgroundColor(QColor("#15191f"))
        main_layout.addWidget(self.web_view)

        self.web_channel = QWebChannel(self.web_view.page())
        self.web_bridge = WebChatBridge()
        self.web_channel.registerObject("bridge", self.web_bridge)
        self.web_view.page().setWebChannel(self.web_channel)
        self.web_bridge.send_requested.connect(self.send_msg)
        self.web_bridge.session_selected.connect(self.session_selected.emit)
        self.web_bridge.session_delete_requested.connect(self.delete_session_requested.emit)
        self.web_bridge.session_rename_requested.connect(self.rename_session_requested.emit)
        self.web_bridge.new_chat_requested.connect(self.new_chat_requested.emit)
        self.web_bridge.ready.connect(self.on_web_ready)
        self.web_view.loadFinished.connect(self.on_web_load_finished)
        self.web_view.setHtml(self.build_chat_html())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "web_view"):
            return
        self.web_view.page().setBackgroundColor(QColor("#15191f"))
        self.web_view.update()
        self.web_view.repaint()
        QTimer.singleShot(0, self.web_view.update)

    def build_chat_html(self):
        ui = {
            "assistantLocal": tr("assistant_local", self.language),
            "newChat": tr("new_chat", self.language),
            "recentSessions": tr("recent_sessions", self.language),
            "searchChats": tr("search_chats", self.language),
            "workspaceLocal": tr("workspace_local", self.language),
            "chatLocal": tr("chat_local", self.language),
            "chatSubtitle": tr("chat_subtitle", self.language),
            "backendBadge": tr("backend_badge", self.language, value=tr("not_selected", self.language)),
            "modelBadge": tr("model_badge", self.language, value=tr("not_selected", self.language)),
            "composerPlaceholder": tr("input_placeholder", self.language),
            "send": tr("send", self.language),
            "emptySearch": tr("empty_search", self.language),
            "emptyChats": tr("empty_chats", self.language),
            "chatActions": tr("chat_actions", self.language),
            "rename": tr("rename", self.language),
            "delete": tr("delete", self.language),
            "renamePrompt": tr("rename_prompt", self.language),
            "deletePrompt": tr("delete_prompt", self.language, label="{label}"),
            "backendPrefix": tr("backend_prefix", self.language),
            "modelPrefix": tr("model_prefix", self.language),
            "dividerResize": tr("divider_resize", self.language),
        }
        html = """<!DOCTYPE html>
<html lang="__LANG__">
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
    .sidebar-search-wrap {
      padding: 0 18px 10px 18px;
    }
    .sidebar-search {
      width: 100%;
      min-height: 38px;
      border: 1px solid #2b3847;
      border-radius: 12px;
      background: rgba(21, 28, 36, 0.92);
      color: #e7eef6;
      font: inherit;
      font-size: 13px;
      padding: 0 12px;
      outline: none;
      box-sizing: border-box;
    }
    .sidebar-search:focus {
      border-color: #4d79a5;
      box-shadow: inset 0 0 0 1px rgba(125, 174, 229, 0.16);
    }
    .sidebar-search::placeholder {
      color: #73879d;
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
    .session-actions {
      position: relative;
      flex: 0 0 auto;
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
    .session-menu-button {
      flex: 0 0 auto;
      min-width: 28px;
      width: 28px;
      height: 28px;
      padding: 0;
      border-radius: 10px;
      background: rgba(36, 47, 60, 0.86);
      color: #94a7bc;
      font-size: 16px;
      font-weight: 700;
      line-height: 1;
      min-width: 28px;
    }
    .session-menu-button:hover {
      background: rgba(55, 69, 86, 0.96);
      color: #eef5fb;
    }
    .session-menu {
      position: absolute;
      top: calc(100% + 6px);
      right: 0;
      min-width: 148px;
      padding: 6px;
      border-radius: 14px;
      border: 1px solid #2b3848;
      background: rgba(15, 21, 28, 0.98);
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28);
      display: none;
      z-index: 30;
    }
    .session-menu.open {
      display: block;
    }
    .session-menu-item {
      width: 100%;
      min-width: 0;
      justify-content: flex-start;
      text-align: left;
      border-radius: 10px;
      padding: 10px 12px;
      background: transparent;
      color: #dce6f0;
      font-size: 12px;
      font-weight: 600;
    }
    .session-menu-item:hover {
      background: rgba(33, 44, 57, 0.96);
    }
    .session-menu-item.destructive {
      color: #ffb8b8;
    }
    .session-menu-item.destructive:hover {
      background: rgba(98, 44, 44, 0.92);
      color: #fff1f1;
    }
    .session-empty {
      padding: 12px 10px;
      color: #7f93a8;
      font-size: 12px;
      line-height: 1.5;
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
        <div class="brand-title">AI Assistant</div>
      </div>
      <button class="new-chat-button" id="new-chat-button" type="button">__NEW_CHAT__</button>
      <div class="sidebar-section">__RECENT_SESSIONS__</div>
      <div class="sidebar-search-wrap">
        <input class="sidebar-search" id="sidebar-search" type="text" placeholder="__SEARCH_CHATS__" />
      </div>
      <div class="session-list" id="session-list"></div>
    </aside>
    <div class="divider" id="sidebar-divider" title="__DIVIDER_RESIZE__"></div>
    <div class="content-shell">
      <header class="topbar">
        <div class="topbar-copy">
          <div class="eyebrow">__WORKSPACE_LOCAL__</div>
          <div class="title" id="chat-title">__CHAT_LOCAL__</div>
        </div>
        <div class="topbar-meta">
          <div class="badge" id="badge-backend">__BACKEND_BADGE__</div>
          <div class="badge" id="badge-model">__MODEL_BADGE__</div>
        </div>
      </header>
      <main class="messages" id="messages"></main>
      <footer class="composer-shell">
        <div class="status" id="status-line"></div>
        <div class="composer-card">
          <form class="composer-form" id="composer-form">
            <textarea id="composer-input" placeholder="__COMPOSER_PLACEHOLDER__"></textarea>
            <button type="submit" id="composer-send">__SEND__</button>
          </form>
        </div>
      </footer>
    </div>
  </div>
  <script>
    const UI = __UI_JSON__;
    let bridge = null;
    let latestState = null;
    let isDraggingDivider = false;
    let sidebarSearchQuery = "";
    function closeAllSessionMenus() {
      document.querySelectorAll(".session-menu.open").forEach((menu) => menu.classList.remove("open"));
    }
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
      const query = sidebarSearchQuery.trim().toLowerCase();
      const filteredSessions = state.sessions.filter((session) => {
        if (!query) return true;
        return (`${session.label} ${session.meta}`).toLowerCase().includes(query);
      });
      if (!filteredSessions.length) {
        const empty = document.createElement("div");
        empty.className = "session-empty";
        empty.textContent = query ? UI.emptySearch : UI.emptyChats;
        list.appendChild(empty);
        return;
      }
      filteredSessions.forEach((session) => {
        const item = document.createElement("div");
        item.className = "session-item" + (session.selected ? " active" : "");
        item.innerHTML = `
          <div class="session-row">
            <div class="session-copy">
              <div class="session-title">${escapeHtml(session.label)}</div>
              <div class="session-meta">${escapeHtml(session.meta)}</div>
            </div>
            <div class="session-actions">
              <button type="button" class="session-menu-button" title="${UI.chatActions}" aria-label="${UI.chatActions}">⋯</button>
              <div class="session-menu">
                <button type="button" class="session-menu-item" data-action="rename">${UI.rename}</button>
                <button type="button" class="session-menu-item destructive" data-action="delete">${UI.delete}</button>
              </div>
            </div>
          </div>`;
        const menuButton = item.querySelector(".session-menu-button");
        const menu = item.querySelector(".session-menu");
        menuButton.addEventListener("click", (event) => {
          event.stopPropagation();
          const isOpen = menu.classList.contains("open");
          closeAllSessionMenus();
          if (!isOpen) menu.classList.add("open");
        });
        menu.querySelector('[data-action="rename"]').addEventListener("click", (event) => {
          event.stopPropagation();
          closeAllSessionMenus();
          const timestampSuffix = new RegExp("\\\\s+\\\\(\\\\d{2}/\\\\d{2}\\\\s+\\\\d{2}:\\\\d{2}\\\\)\\\\s*$");
          const currentLabel = session.label.replace(timestampSuffix, "");
          const renamed = window.prompt(UI.renamePrompt, currentLabel);
          if (renamed && renamed.trim() && bridge) {
            bridge.renameSession(session.index, renamed.trim());
          }
        });
        menu.querySelector('[data-action="delete"]').addEventListener("click", (event) => {
          event.stopPropagation();
          closeAllSessionMenus();
          const confirmed = window.confirm(UI.deletePrompt.replace("{label}", session.label));
          if (confirmed && bridge) bridge.deleteSession(session.index);
        });
        item.addEventListener("click", () => {
          closeAllSessionMenus();
          if (bridge) bridge.openSession(session.index);
        });
        list.appendChild(item);
      });
    }
    function renderState(state) {
      latestState = state;
      document.getElementById("chat-title").textContent = state.title;
      document.getElementById("badge-backend").textContent = UI.backendPrefix + state.backend;
      document.getElementById("badge-model").textContent = UI.modelPrefix + state.model;
      document.getElementById("status-line").textContent = state.status;
      renderSessions(state);
      const messages = document.getElementById("messages");
      messages.innerHTML = "";
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
      const sidebarSearch = document.getElementById("sidebar-search");
      document.getElementById("new-chat-button").addEventListener("click", () => {
        if (bridge) bridge.createNewChat();
      });
      sidebarSearch.addEventListener("input", (event) => {
        sidebarSearchQuery = event.target.value || "";
        if (latestState) renderSessions(latestState);
      });
      document.addEventListener("click", () => {
        closeAllSessionMenus();
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
        return (html
                .replace("__LANG__", self.language)
            .replace("__NEW_CHAT__", ui["newChat"])
            .replace("__RECENT_SESSIONS__", ui["recentSessions"])
            .replace("__SEARCH_CHATS__", ui["searchChats"])
            .replace("__WORKSPACE_LOCAL__", ui["workspaceLocal"])
            .replace("__CHAT_LOCAL__", ui["chatLocal"])
            .replace("__BACKEND_BADGE__", ui["backendBadge"])
            .replace("__MODEL_BADGE__", ui["modelBadge"])
            .replace("__DIVIDER_RESIZE__", ui["dividerResize"])
            .replace("__COMPOSER_PLACEHOLDER__", ui["composerPlaceholder"])
            .replace("__SEND__", ui["send"])
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False)))

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
                "label": tr("you", self.language) if item["role"] == "user" else tr("assistant_local", self.language),
                "html": self.message_to_html(item["content"]),
                "images": image_urls,
            })

        title = tr("active_conversation", self.language) if self.history else tr("chat_local", self.language)
        selected_model_label = tr("selected_model_label", self.language)
        status = tr("status_generating", self.language, model=self.model or selected_model_label) if self.is_generating else (tr("status_ready_model", self.language, model=self.model) if self.model else tr("ready", self.language))
        sessions = []
        for index, session in enumerate(self.sessions_cache):
            real_index = index
            label = session.get("label", tr("session_fallback", self.language, index=real_index + 1))
            meta_parts = []
            if session.get("backend"):
                meta_parts.append(session["backend"])
            if session.get("model"):
                meta_parts.append(session["model"])
            meta = " • ".join(meta_parts) if meta_parts else tr("saved_session", self.language)
            sessions.append({
                "index": real_index,
                "label": label,
                "meta": meta,
                "selected": real_index == self.current_session_idx,
            })
        return {
            "title": title,
            "backend": self.backend or tr("not_selected", self.language),
            "model": self.model or tr("not_selected", self.language),
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
        self.is_generating = False
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
        request_idx = self.idx
        request_model = self.model
        request_backend = self.backend
        self.is_generating = True
        self.render_web_state()
        worker = AIWorker(list(self.history), request_model, request_backend, self.backend_urls, AIBackend.OLLAMA, self.language)
        self.active_workers.append(worker)
        worker.finished.connect(
            lambda text, hist, request_idx=request_idx, request_model=request_model, request_backend=request_backend, worker=worker:
            self.on_res(request_idx, request_model, request_backend, text, hist, worker)
        )
        worker.start()

    def on_res(self, request_idx, request_model, request_backend, text, hist, worker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)

        if 0 <= request_idx < len(self.sessions_cache):
            self.sessions_cache[request_idx]["history"] = hist
            self.sessions_cache[request_idx]["model"] = request_model
            self.sessions_cache[request_idx]["backend"] = request_backend

        if request_idx == self.idx:
            self.history = hist
            self.model = request_model
            self.backend = request_backend
            self.is_generating = False
            self.render_web_state(force_scroll=True)

        self.history_updated.emit(request_idx, hist)


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.active_backend = AIBackend.OLLAMA
        self.active_model = ""
        self.language = "it"
        self.sessions = []
        
        # Load configuration
        self.backend_urls = self.load_config()
        self.language = self.backend_urls.get("language", "it")
        
        # Initialize SQLite database for history
        self.init_db()
        self.load_history_from_db()
        
        self.chat_window = CodexWebChatWindow(self.backend_urls, self.language)
        self.chat_window.session_factory = self.start_new_session_ui
        self.chat_window.history_updated.connect(self.save_updated_history)
        self.chat_window.session_selected.connect(self.restore)
        self.chat_window.delete_session_requested.connect(self.delete_session)
        self.chat_window.rename_session_requested.connect(self.rename_session)
        self.chat_window.new_chat_requested.connect(self.start_new_session_ui)
        
        # Initial Sidebar Population
        self.chat_window.update_sidebar(self.sessions)

        # Gestione Icona (Sia Tray che Finestra)
        icon_path = resource_path("ai_assistant.ico")
        self.app_icon = QIcon(icon_path) if os.path.exists(icon_path) else self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(self.app_icon)
        self.chat_window.setWindowIcon(self.app_icon)
        self.tray_controller = TrayController(self, AIBackend)
        
        self.refresh_mods()
        self.update_menu()
        self.tray.show()

    def start_new_session_ui(self):
        idx = len(self.sessions)
        label = tr("new_chat_label", self.language, timestamp=datetime.now().strftime('%d/%m %H:%M'))
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
        return load_runtime_config(CONFIG_FILE)
    
    def save_config(self, config):
        """Save backend configuration to config.json"""
        try:
            save_runtime_config(config, CONFIG_FILE)
            self.backend_urls = config
            self.language = config.get("language", self.language)
            QMessageBox.information(
                None,
                tr("config_title", self.language),
                tr("config_saved_success", self.language)
            )
        except Exception as e:
            QMessageBox.warning(
                None,
                tr("error", self.language),
                tr("save_error", self.language, message=str(e))
            )
    
    def open_config_dialog(self):
        """Open configuration dialog"""
        # Close search menu to avoid focus issues
        self.tray.contextMenu().hide()
        
        # Create dialog with chat_window as parent if it exists to improve centering
        parent = self.chat_window if self.chat_window.isVisible() else None
        dialog = ConfigDialog(
            self.backend_urls,
            [
                AIBackend.OLLAMA,
                AIBackend.LM_STUDIO,
                AIBackend.LLAMA_CPP,
                AIBackend.LLAMA_SWAP,
                AIBackend.OPENAI_COMPATIBLE,
            ],
            self.language,
            parent,
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            self.save_config(new_config)
            self.chat_window.language = self.language
            self.chat_window.setWindowTitle(tr("window_title", self.language))
            self.chat_window.web_ready = False
            self.chat_window.web_view.setHtml(self.chat_window.build_chat_html())
            self.chat_window.render_web_state()
            self.refresh_mods()
            self.update_menu()

    def open_about_dialog(self):
        self.tray.contextMenu().hide()
        parent = self.chat_window if self.chat_window.isVisible() else None
        dialog = AboutDialog(self.language, parent)
        dialog.setWindowIcon(self.app_icon)
        dialog.exec()

    def load_history_from_disk(self):
        if os.path.exists(HISTORY_FILE):
            self.sessions = load_legacy_history(HISTORY_FILE)

    def init_db(self):
        """Initialize the SQLite database for chat history"""
        try:
            init_db(CHAT_DB_FILE)
        except Exception as e:
            print(f"Error initializing database: {e}")

    def load_history_from_db(self):
        """Load chat history from SQLite database"""
        try:
            self.sessions = load_sessions_from_db(CHAT_DB_FILE)
        except Exception as e:
            print(f"Error loading history from database: {e}")

    def save_updated_history(self, i, h):
        try:
            visible_session = None
            if 0 <= self.chat_window.idx < len(self.sessions):
                visible_session = self.sessions[self.chat_window.idx]

            new_index = persist_session_update(
                self.sessions,
                i,
                h,
                self.active_model,
                self.active_backend,
                CHAT_DB_FILE,
            )

            if visible_session is not None:
                try:
                    selected_index = self.sessions.index(visible_session)
                except ValueError:
                    selected_index = new_index
            else:
                selected_index = new_index

            self.chat_window.idx = selected_index
            self.chat_window.update_sidebar(self.sessions, selected_index)
            return new_index
        except Exception as e:
            print(f"Error saving history to database: {e}")
            return i

    def clear_history_db(self):
        """Clear all history from the database"""
        try:
            clear_history_db(CHAT_DB_FILE)
        except Exception as e:
            print(f"Error clearing database: {e}")

    def rename_session(self, idx, new_label):
        try:
            changed = rename_stored_session(self.sessions, idx, new_label, CHAT_DB_FILE)
            if not changed:
                return
        except Exception as e:
            print(f"Error renaming session in database: {e}")
            return

        self.chat_window.update_sidebar(self.sessions, self.chat_window.idx)
        self.chat_window.render_web_state()

    def delete_session(self, idx):
        try:
            result = delete_stored_session(self.sessions, idx, CHAT_DB_FILE)
        except Exception as e:
            print(f"Error deleting session from database: {e}")
            return

        if result is None:
            return

        if result["session"] is None:
            self.chat_window.update_sidebar([], -1)
            self.chat_window.load_session(-1, [], self.active_model, self.active_backend, is_new=False, bring_forward=False)
            return

        new_idx = result["new_index"]
        self.chat_window.update_sidebar(self.sessions, new_idx)
        target = result["session"]
        self.chat_window.load_session(new_idx, target['history'], target['model'], target['backend'], is_new=False, bring_forward=False)


    def refresh_mods(self):
        return self.tray_controller.refresh_models()

    def update_menu(self):
        self.tray_controller.update_menu()

    def clear_all_history(self):
        if QMessageBox.question(None, tr("clear_history_title", self.language), tr("clear_history_body", self.language), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.sessions = []; self.chat_window.update_sidebar([])
            # Clear database
            self.clear_history_db()
            if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)

    def set_bk(self, b): self.tray_controller.set_backend(b)
    def set_mod(self, x): self.tray_controller.set_model(x)
    def start_vision(self): self.tray_controller.start_vision()
    def start_native_screen_snip(self): self.tray_controller.start_native_screen_snip()
    def poll_native_screen_snip(self): self.tray_controller.poll_native_screen_snip()
    def start_text_grab(self): self.tray_controller.start_text_grab()
    def process(self, data, is_txt): self.tray_controller.process(data, is_txt)
    def restore(self, i): self.tray_controller.restore_session(i)

    def run(self): sys.exit(self.app.exec())

if __name__ == "__main__":
    MainApp().run()
