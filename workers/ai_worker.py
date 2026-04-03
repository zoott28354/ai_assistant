import base64

import ollama
from openai import OpenAI
from PyQt6.QtCore import QThread, pyqtSignal

from core.i18n import tr


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
            if self.backend == self.ollama_backend_name:
                res = ollama.chat(model=self.model, messages=self.history, stream=False)
                answer = res["message"]["content"]
            else:
                base_url = self.backend_urls.get("backends", {}).get(self.backend, "")
                if not base_url:
                    raise Exception(tr("url_not_configured", self.language))

                client = OpenAI(base_url=base_url, api_key="sk-no-key-required")
                msgs = []
                for m in self.history:
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
