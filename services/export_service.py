import base64
import html
import re
import zipfile
from datetime import datetime

from PyQt6.QtGui import QImage, QTextDocument
from PyQt6.QtPrintSupport import QPrinter

from core.i18n import APP_NAME, tr


def safe_filename(value, fallback="chat"):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value or "").strip(" ._")
    name = re.sub(r"\s+", " ", name)
    return (name[:90] or fallback).strip()


def default_export_name(session, extension):
    label = safe_filename(session.get("label", ""), "AI Assistant chat")
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
        content = (message.get("content") or "").strip()
        if content:
            lines.extend([content, ""])
    return "\n".join(lines).rstrip() + "\n", assets


def export_session_to_zip(session, output_path, language="en"):
    markdown_text, assets = build_markdown(session, language=language)
    export_root = safe_filename(default_export_name(session, "export").removesuffix(".export"), "AI Assistant export")
    markdown_name = default_export_name(session, "md")
    instructions = (
        "AI Assistant Obsidian export\n"
        "============================\n\n"
        "Extract this whole folder inside your Obsidian vault.\n"
        "Open the Markdown file from Obsidian.\n"
        "Do not import only the .md file, otherwise image links will be missing.\n"
    )
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{export_root}/{markdown_name}", markdown_text.encode("utf-8"))
        archive.writestr(f"{export_root}/README_IMPORT.txt", instructions.encode("utf-8"))
        for asset_path, data in assets:
            archive.writestr(f"{export_root}/{asset_path}", data)


def _pdf_image_width(data, max_width=620):
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
        "body{font-family:'Segoe UI',Arial,sans-serif;color:#1b2430;font-size:11pt;line-height:1.5;}",
        "h1{font-size:22pt;margin:0 0 6px 0;color:#111827;}",
        ".meta{color:#667085;margin-bottom:18px;}",
        ".msg{border-top:2px solid #d0d7e2;padding-top:10px;margin-top:18px;}",
        ".user{border-color:#e15b5b;}",
        ".assistant{border-color:#3c92dc;}",
        ".role{font-weight:700;text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px;}",
        ".user .role{color:#b53b3b;}",
        ".assistant .role{color:#2676b8;}",
        "pre,code{font-family:Consolas,monospace;background:#f3f5f8;border-radius:4px;padding:2px 4px;}",
        "img{max-width:100%;height:auto;margin:8px 0 12px 0;border:1px solid #e4e7ec;border-radius:8px;}",
        "</style></head><body>",
        f"<h1>{title}</h1>",
        f"<div class='meta'>{html.escape(APP_NAME)}"
        + (f" • {meta}" if meta else "")
        + f" • {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>",
    ]
    for message in session.get("history", []):
        role_key = "user" if message.get("role") == "user" else "assistant"
        role = html.escape(_role_label(message.get("role", ""), language))
        parts.append(f"<section class='msg {role_key}'><div class='role'>{role}</div>")
        for image in message.get("images", []) or []:
            data = _image_bytes(image)
            if data:
                encoded = base64.b64encode(data).decode("ascii")
                width = _pdf_image_width(data)
                parts.append(f"<img width='{width}' src='data:image/png;base64,{encoded}' />")
        content = html.escape(message.get("content") or "").replace("\n", "<br>")
        if content:
            parts.append(f"<div>{content}</div>")
        parts.append("</section>")
    parts.append("</body></html>")
    return "".join(parts)


def export_session_to_pdf(session, output_path, language="en"):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_path)
    document = QTextDocument()
    document.setHtml(_build_pdf_html(session, language=language))
    document.print(printer)
