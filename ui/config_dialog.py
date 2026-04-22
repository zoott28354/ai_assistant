from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.backends import test_backend_connection
from core.config import DEFAULT_CONFIG
from core.i18n import LANGUAGE_LABELS, tr

COMBO_ARROW_PATH = Path(__file__).resolve().parent / "assets" / "combo_arrow_down.svg"


class ConfigDialog(QDialog):
    compact_database_requested = pyqtSignal()
    open_data_folder_requested = pyqtSignal()

    def __init__(self, current_config, backend_names, language="it", parent=None):
        super().__init__(parent)
        self.language = language
        self.backend_names = backend_names
        self.setWindowTitle(tr("config_title", self.language))
        self.resize(900, 620)
        self.setMinimumSize(820, 560)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setStyleSheet("""
            QDialog {
                background-color: #15191f;
                color: #e7edf5;
            }
            QLabel {
                color: #dce6f0;
                font-size: 13px;
            }
            QLabel#dialog_title {
                color: #f3f7fb;
                font-size: 24px;
                font-weight: 800;
            }
            QLabel#dialog_subtitle,
            QLabel#helper_text,
            QLabel#backend_status {
                color: #91a3b7;
                font-size: 12px;
            }
            QLabel#field_label {
                color: #f3f7fb;
                font-size: 13px;
                font-weight: 700;
            }
            QTabWidget::pane {
                border: 1px solid #26313e;
                border-radius: 14px;
                background-color: #171d25;
                top: -1px;
            }
            QTabBar::tab {
                min-width: 116px;
                min-height: 34px;
                padding: 4px 16px;
                margin-right: 6px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                background-color: #202732;
                color: #aab8c8;
                font-weight: 700;
            }
            QTabBar::tab:selected {
                background-color: #263445;
                color: #f3f7fb;
            }
            QLineEdit,
            QComboBox {
                min-height: 40px;
                background-color: #202732;
                color: #eef4fb;
                border: 1px solid #2d3948;
                border-radius: 10px;
                padding: 0 12px;
                selection-background-color: #2d6eb2;
            }
            QLineEdit:focus,
            QComboBox:focus,
            QPlainTextEdit:focus {
                border: 1px solid #4f83b8;
            }
            QComboBox::drop-down {
                border: none;
                width: 34px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QComboBox QAbstractItemView {
                background-color: #1b2430;
                color: #eef4fb;
                border: 1px solid #2d3948;
                selection-background-color: #2d6eb2;
            }
            QPlainTextEdit {
                min-height: 56px;
                max-height: 74px;
                background-color: #202732;
                color: #eef4fb;
                border: 1px solid #2d3948;
                border-radius: 10px;
                padding: 10px 12px;
                selection-background-color: #2d6eb2;
            }
            QPushButton {
                min-height: 40px;
                padding: 0 18px;
                border-radius: 10px;
                background-color: #243142;
                color: #eef4fb;
                border: 1px solid #314457;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #2b3d51;
            }
            QPushButton#test_button {
                min-width: 112px;
                background-color: #1f3850;
                border: 1px solid #2f5678;
            }
            QPushButton#test_button:hover {
                background-color: #284766;
            }
            QDialogButtonBox QPushButton {
                min-width: 118px;
                background-color: #1c7ed6;
                border: none;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #2589e3;
            }
        """)

        self.inputs = {}
        self.status_labels = {}
        self.language_combo = None
        self.backend_combo = None
        self.backend_display_name_edit = None
        self.backend_url_edit = None
        self.backend_api_key_edit = None
        self.backend_note = None
        self.backend_status = None
        self.prompt_inputs = {}

        self.backends = {
            name: current_config.get("backends", {}).get(name, DEFAULT_CONFIG["backends"].get(name, ""))
            for name in self.backend_names
        }
        self.api_keys = {
            name: current_config.get("api_keys", {}).get(name, DEFAULT_CONFIG["api_keys"].get(name, ""))
            for name in DEFAULT_CONFIG["api_keys"]
        }
        self.backend_display_names = current_config.get("backend_display_names", {})
        self.current_language = current_config.get("language", language)
        self.prompts = current_config.get("prompts", DEFAULT_CONFIG.get("prompts", {}))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        title = QLabel(tr("config_heading", self.language))
        title.setObjectName("dialog_title")
        subtitle = QLabel(tr("config_subtitle", self.language))
        subtitle.setObjectName("dialog_subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tabs.addTab(self.build_general_tab(), tr("config_general_tab", self.language))
        tabs.addTab(self.build_backend_tab(), tr("config_local_backend_tab", self.language))
        tabs.addTab(self.build_prompts_tab(), tr("config_prompts_tab", self.language))
        tabs.addTab(self.build_maintenance_tab(), tr("config_maintenance_tab", self.language))
        layout.addWidget(tabs, 1)

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

    def style_combo_arrow(self, combo):
        combo.setStyleSheet("""
            QComboBox {
                padding-right: 34px;
            }
            QComboBox::drop-down {
                border: none;
                width: 34px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QComboBox::down-arrow {
                image: url("%s");
                width: 14px;
                height: 14px;
            }
        """ % COMBO_ARROW_PATH.as_posix())

    def tab_container(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)
        return tab, layout

    def build_general_tab(self):
        tab, layout = self.tab_container()

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        language_title = QLabel(tr("config_language", self.language))
        language_title.setObjectName("field_label")
        self.language_combo = QComboBox()
        self.style_combo_arrow(self.language_combo)
        for code, label in LANGUAGE_LABELS.items():
            self.language_combo.addItem(label, code)
        current_lang_idx = self.language_combo.findData(self.current_language)
        if current_lang_idx >= 0:
            self.language_combo.setCurrentIndex(current_lang_idx)

        form.addRow(language_title, self.language_combo)
        layout.addLayout(form)
        layout.addStretch(1)
        return tab

    def build_maintenance_tab(self):
        tab, layout = self.tab_container()

        title = QLabel(tr("config_maintenance_title", self.language))
        title.setObjectName("field_label")
        layout.addWidget(title)

        help_text = QLabel(tr("config_maintenance_help", self.language))
        help_text.setObjectName("helper_text")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        compact_button = QPushButton(tr("compact_database", self.language))
        compact_button.clicked.connect(self.compact_database_requested.emit)
        action_row.addWidget(compact_button)
        open_folder_button = QPushButton(tr("open_data_folder", self.language))
        open_folder_button.clicked.connect(self.open_data_folder_requested.emit)
        action_row.addWidget(open_folder_button)
        layout.addLayout(action_row)

        layout.addStretch(1)
        return tab

    def build_backend_tab(self):
        tab, layout = self.tab_container()

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        backend_label = QLabel(tr("config_backend_selector", self.language))
        backend_label.setObjectName("field_label")
        self.backend_combo = QComboBox()
        self.style_combo_arrow(self.backend_combo)
        self.backend_combo.addItems(self.backend_names)
        self.backend_combo.currentTextChanged.connect(self.load_backend_fields)
        form.addRow(backend_label, self.backend_combo)

        display_name_label = QLabel(tr("config_backend_display_name", self.language))
        display_name_label.setObjectName("field_label")
        self.backend_display_name_edit = QLineEdit()
        self.backend_display_name_edit.textChanged.connect(self.store_current_backend_display_name)
        form.addRow(display_name_label, self.backend_display_name_edit)

        url_label = QLabel(tr("config_backend_url", self.language))
        url_label.setObjectName("field_label")
        self.backend_url_edit = QLineEdit()
        self.backend_url_edit.textChanged.connect(self.store_current_backend_url)
        form.addRow(url_label, self.backend_url_edit)

        api_key_label = QLabel(tr("config_backend_api_key", self.language))
        api_key_label.setObjectName("field_label")
        self.backend_api_key_edit = QLineEdit()
        self.backend_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.backend_api_key_edit.textChanged.connect(self.store_current_backend_api_key)
        form.addRow(api_key_label, self.backend_api_key_edit)

        layout.addLayout(form)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        test_button = QPushButton(tr("test", self.language))
        test_button.setObjectName("test_button")
        test_button.clicked.connect(self.test_selected_backend)
        action_row.addWidget(test_button)
        layout.addLayout(action_row)

        self.backend_status = QLabel(" ")
        self.backend_status.setObjectName("backend_status")
        self.backend_status.setWordWrap(True)
        layout.addWidget(self.backend_status)

        self.backend_note = QLabel("")
        self.backend_note.setObjectName("helper_text")
        self.backend_note.setWordWrap(True)
        layout.addWidget(self.backend_note)

        layout.addStretch(1)
        self.load_backend_fields(self.backend_combo.currentText())
        return tab

    def build_prompts_tab(self):
        tab, layout = self.tab_container()

        help_text = QLabel(tr("config_prompt_help", self.language))
        help_text.setObjectName("helper_text")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        copied_prompt_label = QLabel(tr("config_copied_text_prompt", self.language))
        copied_prompt_label.setObjectName("field_label")
        copied_prompt_edit = QPlainTextEdit()
        copied_prompt_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        copied_prompt_edit.setPlainText(self.prompts.get("copied_text", ""))
        copied_prompt_edit.setPlaceholderText(tr("analyze_copied_prompt", self.current_language, text="{text}"))
        self.prompt_inputs["copied_text"] = copied_prompt_edit
        layout.addWidget(copied_prompt_label)
        layout.addWidget(copied_prompt_edit)

        image_prompt_label = QLabel(tr("config_image_prompt", self.language))
        image_prompt_label.setObjectName("field_label")
        image_prompt_edit = QPlainTextEdit()
        image_prompt_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        image_prompt_edit.setPlainText(self.prompts.get("image_analysis", ""))
        image_prompt_edit.setPlaceholderText(tr("analyze_image_prompt", self.current_language))
        self.prompt_inputs["image_analysis"] = image_prompt_edit
        layout.addWidget(image_prompt_label)
        layout.addWidget(image_prompt_edit)
        layout.addStretch(1)
        return tab

    def current_backend_name(self):
        return self.backend_combo.currentText() if self.backend_combo else ""

    def store_current_backend_url(self, text):
        name = self.current_backend_name()
        if name:
            self.backends[name] = text.strip()

    def store_current_backend_api_key(self, text):
        name = self.current_backend_name()
        if name:
            self.api_keys[name] = text.strip()

    def store_current_backend_display_name(self, text):
        name = self.current_backend_name()
        if not name:
            return
        display_name = text.strip()
        if display_name and display_name != name:
            self.backend_display_names[name] = display_name
        else:
            self.backend_display_names.pop(name, None)

    def load_backend_fields(self, name):
        if not name or self.backend_url_edit is None or self.backend_api_key_edit is None or self.backend_display_name_edit is None:
            return

        self.backend_display_name_edit.blockSignals(True)
        self.backend_display_name_edit.setText(self.backend_display_names.get(name, name))
        self.backend_display_name_edit.setPlaceholderText(name)
        self.backend_display_name_edit.blockSignals(False)

        self.backend_url_edit.blockSignals(True)
        self.backend_url_edit.setText(self.backends.get(name, ""))
        self.backend_url_edit.setPlaceholderText("https://host:port/v1" if self.is_remote_backend(name) else "")
        self.backend_url_edit.blockSignals(False)

        self.backend_api_key_edit.blockSignals(True)
        self.backend_api_key_edit.setText(self.api_keys.get(name, ""))
        self.backend_api_key_edit.setPlaceholderText(tr("config_api_key_local_placeholder", self.language))
        self.backend_api_key_edit.blockSignals(False)

        if self.backend_status:
            self.backend_status.setText(" ")
            self.backend_status.setStyleSheet("")

        if self.backend_note:
            self.backend_note.setText(self.backend_help_text(name))

    def backend_help_text(self, name):
        if name == "Ollama":
            return tr("config_note_ollama", self.language)
        if name == "LM Studio":
            return tr("config_note_lmstudio", self.language)
        if self.is_remote_backend(name):
            return tr("config_note_openai_compatible", self.language)
        return tr("config_note_local_compatible", self.language)

    def is_remote_backend(self, name):
        lowered = (name or "").lower()
        return "openai" in lowered or "remoto" in lowered or "remote" in lowered

    def test_selected_backend(self):
        name = self.current_backend_name()
        if not name:
            return
        url = self.backends.get(name, "").strip()
        api_key = self.api_keys.get(name, "").strip()
        ok, message = test_backend_connection(
            name,
            url,
            lang=self.language,
            ollama_backend_name=self.backend_names[0],
            api_key=api_key,
        )
        color = "#78d6a4" if ok else "#ff9b9b"
        self.backend_status.setText(message)
        self.backend_status.setStyleSheet(f"color: {color}; font-size: 12px;")

    def test_backend(self, name):
        if self.backend_combo:
            idx = self.backend_combo.findText(name)
            if idx >= 0:
                self.backend_combo.setCurrentIndex(idx)
        self.test_selected_backend()

    def get_config(self):
        return {
            "language": self.language_combo.currentData() if self.language_combo else self.language,
            "backends": self.backends.copy(),
            "api_keys": self.api_keys.copy(),
            "backend_display_names": self.backend_display_names.copy(),
            "prompts": {n: e.toPlainText().strip() for n, e in self.prompt_inputs.items()},
        }
