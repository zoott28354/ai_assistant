import base64
import io
import os
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".tsv",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".ts",
    ".py",
    ".log",
    ".ini",
    ".cfg",
    ".yaml",
    ".yml",
}
DOCUMENT_EXTENSIONS = TEXT_EXTENSIONS | {".docx", ".pdf"}

MAX_TEXT_CHARS = 120_000
PDF_RENDER_DPI = 160


def attachment_file_filter():
    return (
        "Supported files (*.png *.jpg *.jpeg *.webp *.bmp *.gif "
        "*.txt *.md *.markdown *.csv *.tsv *.json *.xml *.html *.htm "
        "*.css *.js *.ts *.py *.log *.ini *.cfg *.yaml *.yml *.docx *.pdf);;"
        "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;"
        "Documents (*.txt *.md *.markdown *.csv *.tsv *.json *.xml *.html *.htm "
        "*.css *.js *.ts *.py *.log *.ini *.cfg *.yaml *.yml *.docx *.pdf);;"
        "All files (*.*)"
    )


def _read_text_file(path):
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read(MAX_TEXT_CHARS)
        except UnicodeDecodeError:
            continue
    with open(path, "rb") as f:
        return f.read(MAX_TEXT_CHARS).decode("utf-8", errors="replace")


def _read_docx(path):
    with zipfile.ZipFile(path) as archive:
        xml_data = archive.read("word/document.xml")
    root = ET.fromstring(xml_data)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace))
        if text.strip():
            paragraphs.append(text)
    return "\n".join(paragraphs)[:MAX_TEXT_CHARS]


def _read_pdf(path):
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError("PDF text extraction requires the optional pypdf package.") from exc

    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
        if sum(len(item) for item in pages) >= MAX_TEXT_CHARS:
            break
    return "\n\n".join(pages).strip()[:MAX_TEXT_CHARS]


def _pdf_pages_to_png_base64(path):
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PDF OCR image rendering requires the optional pymupdf package.") from exc

    pages = []
    document = fitz.open(path)
    try:
        scale = PDF_RENDER_DPI / 72
        matrix = fitz.Matrix(scale, scale)
        for page in document:
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            pages.append(base64.b64encode(pixmap.tobytes("png")).decode("utf-8"))
    finally:
        document.close()
    return pages


def _image_to_png_base64(path):
    with Image.open(path) as image:
        image = image.convert("RGBA")
        output = io.BytesIO()
        image.save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode("utf-8")


def read_attachment(path):
    name = os.path.basename(path)
    extension = os.path.splitext(name)[1].lower()

    if extension in IMAGE_EXTENSIONS:
        return {
            "kind": "image",
            "name": name,
            "data": _image_to_png_base64(path),
        }

    if extension in TEXT_EXTENSIONS:
        return {
            "kind": "document",
            "name": name,
            "content": _read_text_file(path),
            "data": base64.b64encode(open(path, "rb").read()).decode("utf-8"),
        }

    if extension == ".docx":
        return {
            "kind": "document",
            "name": name,
            "content": _read_docx(path),
            "data": base64.b64encode(open(path, "rb").read()).decode("utf-8"),
        }

    if extension == ".pdf":
        try:
            content = _read_pdf(path)
        except Exception as exc:
            content = f"[PDF attached, but text extraction failed: {exc}]"
        ocr_images = []
        if not content or content.startswith("[PDF attached"):
            try:
                ocr_images = _pdf_pages_to_png_base64(path)
            except Exception as exc:
                content = f"{content or '[PDF attached, but no extractable text was found.]'}\n[PDF page rendering failed: {exc}]"
        return {
            "kind": "document",
            "name": name,
            "content": content or "[PDF attached, but no extractable text was found.]",
            "data": base64.b64encode(open(path, "rb").read()).decode("utf-8"),
            "ocr_images": ocr_images,
        }

    raise RuntimeError(f"Unsupported file type: {extension or name}")


def attachment_prompt_text(message, attachments, default_prompt):
    base_message = (message or "").strip() or default_prompt
    document_blocks = []
    image_names = []

    for attachment in attachments:
        if attachment.get("kind") == "image":
            image_names.append(attachment.get("name", "image"))
        elif attachment.get("kind") == "document":
            name = attachment.get("name", "document")
            content = attachment.get("content", "").strip()
            if attachment.get("ocr_images"):
                image_names.append(f"{name} ({len(attachment['ocr_images'])} PDF pages)")
            if content:
                document_blocks.append(f"### {name}\n\n{content}")

    attachment_lines = []
    if image_names:
        attachment_lines.append("Images: " + ", ".join(image_names))
    if document_blocks:
        attachment_lines.append("Documents:\n\n" + "\n\n---\n\n".join(document_blocks))

    if not attachment_lines:
        return base_message

    return f"{base_message}\n\n---\nAttached files:\n" + "\n\n".join(attachment_lines)


def attachment_preview(attachments):
    return [
        {
            "kind": attachment.get("kind", "document"),
            "name": attachment.get("name", "file"),
        }
        for attachment in attachments or []
    ]
