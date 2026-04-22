import base64

import ollama
from openai import OpenAI
from PyQt6.QtCore import QThread, pyqtSignal

from core.i18n import tr
from services.attachment_service import attachment_prompt_text


class AIWorker(QThread):
    finished = pyqtSignal(str, list)

    def __init__(self, history, model, backend, backend_urls, ollama_backend_name, language="it"):
        super().__init__()
        self.history = history
        self.model = model
        self.backend = backend
        self.backend_urls = backend_urls
        self.ollama_backend_name = ollama_backend_name
        self.language = language

    def run(self):
        try:
            request_history = []
            for message in self.history:
                prepared = dict(message)
                ocr_images = []
                for attachment in message.get("attachments", []) or []:
                    ocr_images.extend(attachment.get("ocr_images", []) or [])
                if ocr_images:
                    prepared["images"] = list(prepared.get("images", []) or []) + ocr_images
                prepared["content"] = attachment_prompt_text(
                    message.get("content", ""),
                    message.get("attachments", []),
                    tr("attachments_default_prompt", self.language),
                )
                prepared.pop("attachments", None)
                request_history.append(prepared)

            if self.backend == self.ollama_backend_name:
                res = ollama.chat(model=self.model, messages=request_history, stream=False)
                answer = res["message"]["content"]
            else:
                base_url = self.backend_urls.get("backends", {}).get(self.backend, "")
                if not base_url:
                    raise Exception(tr("url_not_configured", self.language))

                api_key = self.backend_urls.get("api_keys", {}).get(self.backend, "").strip()
                client = OpenAI(base_url=base_url, api_key=api_key or "sk-no-key-required")
                msgs = []
                for m in request_history:
                    if "images" in m and m["images"]:
                        content = [{"type": "text", "text": m["content"]}]
                        for img in m["images"]:
                            b64 = img if isinstance(img, str) else base64.b64encode(img).decode("utf-8")
                            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
                        msgs.append({"role": m["role"], "content": content})
                    else:
                        msgs.append({"role": m["role"], "content": m["content"]})
                comp = client.chat.completions.create(model=self.model, messages=msgs)
                answer = comp.choices[0].message.content

            self.history.append({"role": "assistant", "content": answer})
            self.finished.emit(answer, self.history)
        except Exception as e:
            self.finished.emit(tr("error_backend", self.language, backend=self.backend, message=str(e)), self.history)
