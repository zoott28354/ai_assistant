from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from core.backends import test_backend_connection
from core.config import DEFAULT_CONFIG
from core.i18n import LANGUAGE_LABELS, tr


class ConfigDialog(QDialog):
    def __init__(self, current_config, backend_names, language="it", parent=None):
        super().__init__(parent)
        self.language = language
        self.backend_names = backend_names
        self.setWindowTitle(tr("config_title", self.language))
        self.resize(760, 640)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowSystemMenuHint | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #15191f;
                color: #e7edf5;
            }
            QLabel {
                color: #dce6f0;
            }
            QLabel#dialog_title {
                color: #f3f7fb;
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#dialog_subtitle {
                color: #91a3b7;
                font-size: 12px;
            }
            QLabel[role="backend_name"] {
                color: #f3f7fb;
                font-size: 13px;
                font-weight: 700;
                padding-top: 8px;
            }
            QLabel[role="backend_status"] {
                color: #8ea1b5;
                font-size: 11px;
                padding: 1px 2px 0 2px;
            }
            QLineEdit {
                min-height: 38px;
                background-color: #202732;
                color: #eef4fb;
                border: 1px solid #2d3948;
                border-radius: 10px;
                padding: 0 12px;
                selection-background-color: #2d6eb2;
            }
            QLineEdit:focus {
                border: 1px solid #4f83b8;
            }
            QComboBox {
                min-height: 38px;
                background-color: #202732;
                color: #eef4fb;
                border: 1px solid #2d3948;
                border-radius: 10px;
                padding: 0 12px;
            }
            QComboBox:focus {
                border: 1px solid #4f83b8;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox QAbstractItemView {
                background-color: #1b2430;
                color: #eef4fb;
                border: 1px solid #2d3948;
                selection-background-color: #2d6eb2;
            }
            QPlainTextEdit {
                min-height: 92px;
                background-color: #202732;
                color: #eef4fb;
                border: 1px solid #2d3948;
                border-radius: 10px;
                padding: 10px 12px;
                selection-background-color: #2d6eb2;
            }
            QPlainTextEdit:focus {
                border: 1px solid #4f83b8;
            }
            QPushButton {
                min-height: 38px;
                padding: 0 16px;
                border-radius: 10px;
                background-color: #243142;
                color: #eef4fb;
                border: 1px solid #314457;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #2b3d51;
            }
            QPushButton#test_button {
                min-width: 86px;
                background-color: #1f3850;
                border: 1px solid #2f5678;
            }
            QPushButton#test_button:hover {
                background-color: #284766;
            }
            QDialogButtonBox QPushButton {
                min-width: 112px;
                background-color: #1c7ed6;
                border: none;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #2589e3;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        title = QLabel(tr("config_heading", self.language))
        title.setObjectName("dialog_title")
        subtitle = QLabel(tr("config_subtitle", self.language))
        subtitle.setObjectName("dialog_subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(1, 1)

        self.inputs = {}
        self.status_labels = {}
        self.language_combo = None
        self.prompt_inputs = {}
        backends = current_config.get("backends", {})
        current_language = current_config.get("language", language)
        prompts = current_config.get("prompts", DEFAULT_CONFIG.get("prompts", {}))

        row = 0
        language_title = QLabel(tr("config_language", self.language))
        language_title.setProperty("role", "backend_name")
        self.language_combo = QComboBox()
        for code, label in LANGUAGE_LABELS.items():
            self.language_combo.addItem(label, code)
        current_lang_idx = self.language_combo.findData(current_language)
        if current_lang_idx >= 0:
            self.language_combo.setCurrentIndex(current_lang_idx)
        grid.addWidget(language_title, row, 0, 1, 1)
        grid.addWidget(self.language_combo, row, 1, 1, 2)
        language_status_spacer = QLabel(" ")
        language_status_spacer.setProperty("role", "backend_status")
        grid.addWidget(language_status_spacer, row + 1, 1, 1, 2)
        row += 2

        for name in self.backend_names:
            url = backends.get(name, DEFAULT_CONFIG["backends"].get(name, ""))
            title_label = QLabel(name)
            title_label.setProperty("role", "backend_name")

            edit = QLineEdit(url)
            if "OpenAI" in name:
                edit.setPlaceholderText("https://host:port/v1")
            self.inputs[name] = edit

            test_button = QPushButton(tr("test", self.language))
            test_button.setObjectName("test_button")
            test_button.clicked.connect(partial(self.test_backend, name))

            status = QLabel(" ")
            status.setProperty("role", "backend_status")
            self.status_labels[name] = status

            grid.addWidget(title_label, row, 0, 1, 1)
            grid.addWidget(edit, row, 1, 1, 1)
            grid.addWidget(test_button, row, 2, 1, 1)
            grid.addWidget(status, row + 1, 1, 1, 2)
            row += 2

        layout.addLayout(grid)

        notes = QLabel(tr("config_notes", self.language))
        notes.setWordWrap(True)
        notes.setObjectName("dialog_subtitle")
        layout.addWidget(notes)

        prompt_title = QLabel(tr("config_custom_prompts", self.language))
        prompt_title.setProperty("role", "backend_name")
        layout.addWidget(prompt_title)

        copied_prompt_label = QLabel(tr("config_copied_text_prompt", self.language))
        copied_prompt_label.setProperty("role", "backend_name")
        copied_prompt_edit = QPlainTextEdit()
        copied_prompt_edit.setPlainText(prompts.get("copied_text", ""))
        copied_prompt_edit.setPlaceholderText(tr("analyze_copied_prompt", current_language, text="{text}"))
        self.prompt_inputs["copied_text"] = copied_prompt_edit
        layout.addWidget(copied_prompt_label)
        layout.addWidget(copied_prompt_edit)

        image_prompt_label = QLabel(tr("config_image_prompt", self.language))
        image_prompt_label.setProperty("role", "backend_name")
        image_prompt_edit = QPlainTextEdit()
        image_prompt_edit.setPlainText(prompts.get("image_analysis", ""))
        image_prompt_edit.setPlaceholderText(tr("analyze_image_prompt", current_language))
        self.prompt_inputs["image_analysis"] = image_prompt_edit
        layout.addWidget(image_prompt_label)
        layout.addWidget(image_prompt_edit)

        layout.addStretch(1)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = btns.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = btns.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText(tr("ok", self.language))
        if cancel_button:
            cancel_button.setText(tr("cancel", self.language))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def test_backend(self, name):
        edit = self.inputs[name]
        status_label = self.status_labels[name]
        ok, message = test_backend_connection(name, edit.text().strip(), lang=self.language, ollama_backend_name=self.backend_names[0])
        color = "#78d6a4" if ok else "#ff9b9b"
        status_label.setText(message)
        status_label.setStyleSheet(f"color: {color}; font-size: 11px; padding: 1px 2px 0 2px;")

    def get_config(self):
        return {
            "language": self.language_combo.currentData() if self.language_combo else self.language,
            "backends": {n: e.text().strip() for n, e in self.inputs.items()},
            "prompts": {n: e.toPlainText().strip() for n, e in self.prompt_inputs.items()},
        }
