import json
import os
import shutil
import sys

from .i18n import APP_NAME

PORTABLE_MARKER = "portable_mode.flag"
HISTORY_FILE_NAME = "history_db.json"
CONFIG_FILE_NAME = "config.json"
CHAT_DB_FILE_NAME = "chat_history.db"

DEFAULT_CONFIG = {
    "language": "it",
    "active_backend": "Ollama",
    "active_model": "",
    "backends": {
        "Ollama": "http://localhost:11434",
        "LM Studio": "http://localhost:1234/v1",
        "Llama.cpp": "http://localhost:8033/v1",
        "Llama-Swap": "http://localhost:8080/v1",
        "Custom 1": "",
        "Custom 2": "",
    },
    "api_keys": {
        "Ollama": "",
        "LM Studio": "",
        "Llama.cpp": "",
        "Llama-Swap": "",
        "Custom 1": "",
        "Custom 2": "",
    },
    "prompts": {
        "copied_text": "",
        "image_analysis": "",
    },
}


def get_runtime_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_user_data_dir():
    if sys.platform.startswith("win"):
        base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base_dir = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base_dir, APP_NAME)


def get_app_data_dir():
    runtime_dir = get_runtime_dir()
    portable_marker = os.path.join(runtime_dir, PORTABLE_MARKER)
    if getattr(sys, "frozen", False):
        if os.path.exists(portable_marker):
            return runtime_dir
        return get_user_data_dir()
    return os.path.dirname(runtime_dir)


def ensure_app_data_dir():
    data_dir = get_app_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def migrate_storage_file(filename, target_dir):
    target_path = os.path.join(target_dir, filename)
    if os.path.exists(target_path):
        return target_path

    candidate_dirs = []
    runtime_dir = get_runtime_dir()
    current_dir = os.path.abspath(os.getcwd())
    for candidate in (runtime_dir, current_dir):
        if candidate and candidate not in candidate_dirs:
            candidate_dirs.append(candidate)

    for candidate_dir in candidate_dirs:
        source_path = os.path.join(candidate_dir, filename)
        if not os.path.exists(source_path) or os.path.abspath(source_path) == os.path.abspath(target_path):
            continue
        try:
            shutil.copy2(source_path, target_path)
            return target_path
        except Exception as exc:
            print(f"Warning: unable to migrate {filename}: {exc}")
            break

    return target_path


APP_DATA_DIR = ensure_app_data_dir()
HISTORY_FILE = migrate_storage_file(HISTORY_FILE_NAME, APP_DATA_DIR)
CONFIG_FILE = migrate_storage_file(CONFIG_FILE_NAME, APP_DATA_DIR)
CHAT_DB_FILE = migrate_storage_file(CHAT_DB_FILE_NAME, APP_DATA_DIR)


def load_runtime_config(config_path=CONFIG_FILE):
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "language": data.get("language", DEFAULT_CONFIG["language"]),
                    "active_backend": data.get("active_backend", DEFAULT_CONFIG["active_backend"]),
                    "active_model": data.get("active_model", DEFAULT_CONFIG["active_model"]),
                    "backends": {**DEFAULT_CONFIG["backends"], **data.get("backends", {})},
                    "api_keys": {**DEFAULT_CONFIG["api_keys"], **data.get("api_keys", {})},
                    "backend_display_names": data.get("backend_display_names", {}),
                    "prompts": {**DEFAULT_CONFIG["prompts"], **data.get("prompts", {})},
                }
        except Exception:
            pass
    return {
        "language": DEFAULT_CONFIG["language"],
        "active_backend": DEFAULT_CONFIG["active_backend"],
        "active_model": DEFAULT_CONFIG["active_model"],
        "backends": DEFAULT_CONFIG["backends"].copy(),
        "api_keys": DEFAULT_CONFIG["api_keys"].copy(),
        "backend_display_names": {},
        "prompts": DEFAULT_CONFIG["prompts"].copy(),
    }


def save_runtime_config(config, config_path=CONFIG_FILE):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
