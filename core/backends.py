import requests
import ollama

from .i18n import tr


def openai_models_url(base_url):
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/v1"):
        return f"{base}/models"
    return f"{base}/v1/models"


def test_backend_connection(backend_name, url, timeout=4, lang="it", ollama_backend_name="Ollama"):
    cleaned_url = (url or "").strip()
    if not cleaned_url:
        return False, tr("url_not_configured", lang)

    try:
        if backend_name == ollama_backend_name:
            response = requests.get(f"{cleaned_url.rstrip('/')}/api/tags", timeout=timeout)
            response.raise_for_status()
            models = [m.get("model", "") for m in response.json().get("models", []) if m.get("model")]
        else:
            response = requests.get(openai_models_url(cleaned_url), timeout=timeout)
            response.raise_for_status()
            models = [m.get("id", "") for m in response.json().get("data", []) if m.get("id")]
        if models:
            return True, tr("models_found", lang, count=len(models))
        return True, tr("connected_no_models", lang)
    except requests.exceptions.Timeout:
        return False, tr("timeout", lang)
    except requests.exceptions.ConnectionError:
        return False, tr("offline", lang)
    except requests.exceptions.HTTPError:
        return False, tr("invalid_response", lang)
    except Exception:
        return False, tr("connection_failed", lang)


def fetch_backend_models(active_backend, backend_urls, active_model="", timeout=4, lang="it", ollama_backend_name="Ollama"):
    try:
        if active_backend == ollama_backend_name:
            base_url = backend_urls.get("backends", {}).get(active_backend, "").strip()
            if base_url:
                response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
                response.raise_for_status()
                models = [m.get("model") for m in response.json().get("models", []) if m.get("model")]
            else:
                models = [m["model"] if isinstance(m, dict) else m.model for m in ollama.list().get("models", [])]
        else:
            base_url = backend_urls.get("backends", {}).get(active_backend, "").strip()
            if not base_url:
                return [tr("url_not_configured", lang)], active_model
            response = requests.get(openai_models_url(base_url), timeout=timeout)
            response.raise_for_status()
            models = [m.get("id") for m in response.json().get("data", []) if m.get("id")]

        if models and active_model not in models:
            active_model = models[0]
        return models or [tr("connected_no_models", lang)], active_model
    except Exception:
        return [tr("offline", lang)], active_model
