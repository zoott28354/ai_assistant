import os
import time
from datetime import datetime

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from core.backends import fetch_backend_models
from core.i18n import tr
from services.capture_service import image_to_png_bytes, start_native_screen_snip
from services.clipboard_service import copy_selection_and_get_text, get_clipboard_image_hash, get_new_clipboard_image
from services.tray_service import build_tray_menu
from ui.snipping_tool import SnippingTool


class TrayController:
    def __init__(self, owner, backend_enum):
        self.owner = owner
        self.backend_enum = backend_enum
        self.native_snip_timer = None
        self.native_snip_deadline = 0
        self.native_snip_last_hash = None
        self.snipper = None

    def refresh_models(self):
        models, selected_model = fetch_backend_models(
            self.owner.active_backend,
            self.owner.backend_urls,
            self.owner.active_model,
            lang=self.owner.language,
            ollama_backend_name=self.backend_enum.OLLAMA,
        )
        self.owner.active_model = selected_model
        return models

    def update_menu(self):
        build_tray_menu(
            self.owner.language,
            self.owner.tray,
            self.owner.active_backend,
            self.owner.active_model,
            self.owner.backend_urls,
            [
                self.backend_enum.OLLAMA,
                self.backend_enum.LM_STUDIO,
                self.backend_enum.LLAMA_CPP,
                self.backend_enum.LLAMA_SWAP,
            ],
            self.backend_enum.OPENAI_COMPATIBLE,
            self.refresh_models(),
            {
                "start_vision": self.start_vision,
                "start_text_grab": self.start_text_grab,
                "open_chat": self.owner.chat_window.show,
                "open_config": self.owner.open_config_dialog,
                "set_backend": self.set_backend,
                "set_model": self.set_model,
                "quit_app": self.owner.app.quit,
            },
        )

    def set_backend(self, backend):
        self.owner.active_backend = backend
        self.refresh_models()
        self.update_menu()

    def set_model(self, model):
        self.owner.active_model = model
        self.update_menu()

    def start_vision(self):
        self.owner.tray.contextMenu().hide()
        QApplication.processEvents()
        time.sleep(0.15)
        self.start_native_screen_snip()

    def start_native_screen_snip(self):
        self.native_snip_last_hash = get_clipboard_image_hash()
        self.native_snip_deadline = time.time() + 20
        if self.native_snip_timer is None:
            self.native_snip_timer = QTimer()
            self.native_snip_timer.setInterval(250)
            self.native_snip_timer.timeout.connect(self.poll_native_screen_snip)
        self.native_snip_timer.start()
        try:
            start_native_screen_snip()
        except OSError:
            self.native_snip_timer.stop()
            self.snipper = SnippingTool(self.process)

    def poll_native_screen_snip(self):
        if time.time() > self.native_snip_deadline:
            self.native_snip_timer.stop()
            return

        image, current_hash = get_new_clipboard_image(self.native_snip_last_hash)
        if image is None:
            return

        self.native_snip_timer.stop()
        self.native_snip_last_hash = current_hash
        self.process(image_to_png_bytes(image), False)

    def start_text_grab(self):
        self.owner.tray.contextMenu().hide()
        QApplication.processEvents()
        time.sleep(0.4)
        text = copy_selection_and_get_text(0.3)
        if text.strip():
            self.process(tr("analyze_copied_prompt", self.owner.language, text=text), True)

    def process(self, data, is_txt):
        idx = len(self.owner.sessions)
        if is_txt:
            history = [{"role": "user", "content": data}]
            label = data[:30] + "..." if len(data) > 30 else data
        else:
            prompt = tr("analyze_image_prompt", self.owner.language)
            history = [{"role": "user", "content": prompt, "images": [data]}]
            label = tr("image_analysis_label", self.owner.language)

        self.owner.sessions.append(
            {
                "label": f"{label} ({datetime.now().strftime('%d/%m %H:%M')})",
                "history": history,
                "model": self.owner.active_model,
                "backend": self.owner.active_backend,
            }
        )
        new_idx = self.owner.save_updated_history(idx, history)
        if new_idx < 0:
            new_idx = idx
        self.owner.chat_window.update_sidebar(self.owner.sessions, new_idx)
        self.owner.chat_window.load_session(
            new_idx,
            history,
            self.owner.active_model,
            self.owner.active_backend,
            is_new=True,
            bring_forward=True,
        )

    def restore_session(self, idx):
        session = self.owner.sessions[idx]
        self.owner.chat_window.load_session(
            idx,
            session["history"],
            session["model"],
            session["backend"],
            bring_forward=False,
        )
