from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from core.i18n import APP_NAME, APP_VERSION, tr


class AboutDialog(QDialog):
    def __init__(self, language="it", parent=None, on_check_updates=None):
        super().__init__(parent)
        self.language = language
        self.on_check_updates = on_check_updates
        self.setWindowTitle(tr("about_title", self.language))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumWidth(460)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #15191f;
                color: #e7edf5;
            }
            QLabel {
                color: #dce6f0;
                font-size: 13px;
            }
            QLabel#about_title {
                color: #f3f7fb;
                font-size: 24px;
                font-weight: 700;
            }
            QLabel#about_meta {
                color: #8ea1b5;
                font-size: 12px;
            }
            QLabel#about_desc {
                color: #dce6f0;
                font-size: 13px;
                line-height: 1.5;
            }
            QLabel#about_link {
                color: #77b7ff;
                font-size: 13px;
            }
            QLabel#about_link a {
                color: #77b7ff;
                text-decoration: none;
            }
            QLabel#about_link a:hover {
                text-decoration: underline;
            }
            QDialogButtonBox QPushButton {
                min-width: 112px;
                min-height: 38px;
                background-color: #1c7ed6;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-weight: 700;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #2589e3;
            }
            """
        )

        github_url = "https://github.com/zoott28354/ai_assistant"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(10)

        title = QLabel(APP_NAME)
        title.setObjectName("about_title")

        version = QLabel(tr("about_version", self.language, version=APP_VERSION))
        version.setObjectName("about_meta")

        description = QLabel(tr("about_description", self.language))
        description.setObjectName("about_desc")
        description.setWordWrap(True)

        author = QLabel(tr("about_author", self.language, author="zoott28354"))
        license_label = QLabel(tr("about_license", self.language, license_name="MIT"))

        github = QLabel(
            f'{tr("about_github", self.language)}: '
            f'<a href="{github_url}">zoott28354/ai_assistant</a>'
        )
        github.setObjectName("about_link")
        github.setOpenExternalLinks(True)
        github.setTextFormat(Qt.TextFormat.RichText)
        github.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addSpacing(2)
        layout.addWidget(description)
        layout.addSpacing(4)
        layout.addWidget(author)
        layout.addWidget(license_label)
        layout.addWidget(github)
        layout.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        update_button = buttons.addButton(
            tr("about_check_updates", self.language),
            QDialogButtonBox.ButtonRole.ActionRole,
        )
        update_button.clicked.connect(self.check_updates)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText(tr("ok", self.language))
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def check_updates(self):
        if self.on_check_updates:
            self.on_check_updates()
