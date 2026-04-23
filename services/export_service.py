import base64
import html
import re
import zipfile
from datetime import datetime

import markdown
from PyQt6.QtCore import QMarginsF, QObject, QUrl, pyqtSignal
from PyQt6.QtGui import QImage, QPageLayout, QPageSize
from PyQt6.QtWebEngineCore import QWebEnginePage

from core.i18n import APP_NAME, tr


def safe_filename(value, fallback="chat"):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value or "").strip(" ._")
    name = re.sub(r"\s+", " ", name)
    return (name[:90] or fallback).strip()


def default_export_name(session, extension):
    label = safe_filename(session.get("label", ""), f"{APP_NAME} chat")
    stamp = _session_stamp(session)
    return f"{label} - {stamp}.{extension}"


def _session_stamp(session):
    raw_date = session.get("created_at") or session.get("updated_at") or ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw_date.split(".")[0], fmt).strftime("%Y%m%d-%H%M")
        except Exception:
            pass
    return datetime.now().strftime("%Y%m%d-%H%M")


def _image_bytes(image):
    if isinstance(image, bytes):
        return image
    if isinstance(image, str):
        return base64.b64decode(image)
    return b""


def _attachment_bytes(attachment):
    data = attachment.get("data", "")
    if isinstance(data, bytes):
        return data
    if isinstance(data, str) and data:
        return base64.b64decode(data)
    return b""


def _role_label(role, language):
    return tr("you", language) if role == "user" else tr("assistant_local", language)


def build_markdown(session, language="en", asset_prefix="assets"):
    title = session.get("label") or tr("session_fallback", language, index=session.get("id") or 1)
    lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f'source: "{APP_NAME}"',
        f'exported: "{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"',
        f'backend: "{session.get("backend") or ""}"',
        f'model: "{session.get("model") or ""}"',
        "---",
        "",
        f"# {title}",
        "",
    ]
    assets = []
    image_counter = 1
    for message_index, message in enumerate(session.get("history", []), start=1):
        role = _role_label(message.get("role", ""), language)
        lines.extend([f"## {role}", ""])
        for image in message.get("images", []) or []:
            data = _image_bytes(image)
            if not data:
                continue
            image_name = f"image-{message_index:03d}-{image_counter:03d}.png"
            assets.append((f"{asset_prefix}/{image_name}", data))
            lines.extend([f"![{image_name}]({asset_prefix}/{image_name})", ""])
            image_counter += 1
        attachments = message.get("attachments", []) or []
        if attachments:
            lines.extend(["**Attachments**", ""])
            for attachment_index, attachment in enumerate(attachments, start=1):
                name = attachment.get("name", "file")
                asset_name = f"attachment-{message_index:03d}-{attachment_index:03d}-{safe_filename(name, 'attachment')}"
                data = _attachment_bytes(attachment)
                if data:
                    asset_path = f"{asset_prefix}/{asset_name}"
                    assets.append((asset_path, data))
                    lines.append(f"- [{name}]({asset_path})")
                else:
                    lines.append(f"- {name}")
            lines.append("")
        content = (message.get("content") or "").strip()
        if content:
            lines.extend([content, ""])
    return "\n".join(lines).rstrip() + "\n", assets


def export_session_to_zip(session, output_path, language="en"):
    markdown_text, assets = build_markdown(session, language=language)
    export_root = safe_filename(default_export_name(session, "export").removesuffix(".export"), f"{APP_NAME} export")
    markdown_name = default_export_name(session, "md")
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{export_root}/{markdown_name}", markdown_text.encode("utf-8"))
        for asset_path, data in assets:
            archive.writestr(f"{export_root}/{asset_path}", data)


def _pdf_image_width(data, max_width=760):
    image = QImage()
    if not image.loadFromData(data):
        return max_width
    if image.width() <= 0:
        return max_width
    return min(image.width(), max_width)


def _build_pdf_html(session, language="en"):
    title = html.escape(session.get("label") or tr("session_fallback", language, index=session.get("id") or 1))
    meta = html.escape(" • ".join(part for part in [session.get("backend"), session.get("model")] if part))
    parts = [
        "<html><head><meta charset='utf-8'><style>",
        "@page{size:A4;margin:10mm 16mm 14mm 16mm;}",
        "body{font-family:'Segoe UI',Arial,sans-serif;color:#17202b;background:#ffffff;font-size:11pt;line-height:1.52;}",
        ".page{background:#ffffff;padding:10px 8px;}",
        "h1{font-size:22pt;margin:0 0 6px 0;color:#111827;}",
        ".meta{color:#667085;margin-bottom:18px;font-size:9.5pt;}",
        ".msg{margin:0 0 16px 0;padding:0;page-break-inside:auto;}",
        ".role-row{display:table;width:100%;margin-bottom:10px;}",
        ".role{display:table-cell;width:1%;white-space:nowrap;font-weight:800;text-transform:uppercase;letter-spacing:.05em;font-size:10pt;padding-right:10px;}",
        ".line{display:table-cell;height:1px;border-top:2px solid #63b3ff;vertical-align:middle;}",
        ".user .role{color:#ff9f9f;}",
        ".assistant .role{color:#a9d0ff;}",
        ".user .line{border-top-color:#ea5a5a;}",
        ".assistant .line{border-top-color:#63b3ff;}",
        ".body{color:#243244;font-size:11pt;}",
        ".user .body{color:#111827;}",
        ".body p{margin:0 0 10px 0;}",
        ".body ul,.body ol{margin:8px 0 12px 22px;padding:0;}",
        ".body li{margin:4px 0;}",
        ".body blockquote{margin:10px 0;padding:8px 12px;border-left:3px solid #94a3b8;background:#f1f5f9;color:#334155;}",
        ".body pre{margin:12px 0;padding:12px 14px;border-radius:10px;border:1px solid #d0d7e2;background:#f8fafc;color:#17202b;white-space:pre-wrap;}",
        ".body code{font-family:Consolas,monospace;background:#eef2f7;color:#164b78;border-radius:5px;padding:2px 5px;}",
        ".body pre code{background:transparent;color:inherit;padding:0;}",
        ".image-wrap{margin:4px 0 8px 0;page-break-inside:avoid;}",
        ".attachments{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 10px 0;}",
        ".attachment{display:inline-block;border:1px solid #cbd5e1;border-radius:999px;background:#f8fafc;color:#334155;padding:5px 9px;font-size:9.5pt;font-weight:700;}",
        "img{max-width:100%;height:auto;border:1px solid #d0d7e2;border-radius:8px;background:#f8fafc;}",
        "</style></head><body>",
        "<div class='page'>",
        f"<h1>{title}</h1>",
        f"<div class='meta'>{html.escape(APP_NAME)}"
        + (f" • {meta}" if meta else "")
        + f" • {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>",
    ]
    for message in session.get("history", []):
        role_key = "user" if message.get("role") == "user" else "assistant"
        role = html.escape(_role_label(message.get("role", ""), language))
        parts.append(
            f"<section class='msg {role_key}'>"
            f"<div class='role-row'><span class='role'>{role}</span><span class='line'></span></div>"
        )
        for image in message.get("images", []) or []:
            data = _image_bytes(image)
            if data:
                encoded = base64.b64encode(data).decode("ascii")
                width = _pdf_image_width(data)
                parts.append(f"<div class='image-wrap'><img width='{width}' src='data:image/png;base64,{encoded}' /></div>")
        attachments = message.get("attachments", []) or []
        if attachments:
            parts.append("<div class='attachments'>")
            for attachment in attachments:
                name = html.escape(attachment.get("name", "file"))
                parts.append(f"<span class='attachment'>📄 {name}</span>")
            parts.append("</div>")
        content = markdown.markdown(
            message.get("content") or "",
            extensions=["fenced_code", "tables", "nl2br"],
            output_format="html5",
        )
        if content:
            parts.append(f"<div class='body'>{content}</div>")
        parts.append("</section>")
    parts.append("</div></body></html>")
    return "".join(parts)


class PdfExportJob(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, session, output_path, language="en", parent=None):
        super().__init__(parent)
        self.session = session
        self.output_path = output_path
        self.language = language
        self.page = QWebEnginePage(self)
        self.page.loadFinished.connect(self._on_load_finished)
        self.page.pdfPrintingFinished.connect(self._on_pdf_finished)

    def start(self):
        self.page.setHtml(_build_pdf_html(self.session, self.language), QUrl("about:blank"))

    def _on_load_finished(self, ok):
        if not ok:
            self.finished.emit(False, "Unable to render export HTML.")
            return
        layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(16, 10, 16, 14),
            QPageLayout.Unit.Millimeter,
        )
        self.page.printToPdf(self.output_path, layout)

    def _on_pdf_finished(self, _path, success):
        if success:
            self.finished.emit(True, "")
        else:
            self.finished.emit(False, "Unable to write PDF file.")


def export_session_to_pdf(session, output_path, language="en"):
    job = PdfExportJob(session, output_path, language)
    job.start()
    return job
