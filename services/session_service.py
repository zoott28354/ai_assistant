import base64
import json
import os
import re
import sqlite3
from datetime import datetime

LABEL_TIMESTAMP_RE = re.compile(r"\s*\(\d{2}/\d{2}\s+\d{2}:\d{2}\)\s*$")


def _strip_label_timestamp(label):
    return LABEL_TIMESTAMP_RE.sub("", label or "").strip()


def _is_default_session_label(label):
    return (
        label.startswith("Nuova chat (")
        or label.startswith("New chat (")
        or label.startswith("Ciao! Come posso aiutarti oggi?")
    )


def _label_with_timestamp(label, timestamp=None):
    base_label = _strip_label_timestamp(label) or "Chat"
    stamp = (timestamp or datetime.now()).strftime("%d/%m %H:%M")
    return f"{base_label} ({stamp})"


def load_legacy_history(history_file):
    if not os.path.exists(history_file):
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        for session in loaded:
            for message in session.get("history", []):
                if "images" in message:
                    message["images"] = [base64.b64decode(img) for img in message["images"]]
        return loaded
    except Exception:
        return []


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            model TEXT,
            backend TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_deleted INTEGER DEFAULT 0
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
        """
    )
    conn.commit()
    conn.close()


def load_sessions_from_db(db_path):
    sessions = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, label, model, backend, created_at, updated_at
        FROM sessions
        WHERE is_deleted = 0
        ORDER BY updated_at DESC, created_at DESC, id DESC
        """
    )
    sessions_data = cursor.fetchall()

    for session_id, label, model, backend, created_at, updated_at in sessions_data:
        cursor.execute(
            """
            SELECT role, content, images
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        )
        messages_data = cursor.fetchall()

        history = []
        for role, content, images in messages_data:
            message = {"role": role, "content": content}
            if images:
                try:
                    image_list = json.loads(images)
                    message["images"] = [base64.b64decode(img) for img in image_list]
                except Exception:
                    pass
            history.append(message)

        sessions.append(
            {
                "id": session_id,
                "label": label,
                "model": model,
                "backend": backend,
                "history": history,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    conn.close()
    return sessions


def sort_sessions(sessions, current_session=None):
    def sort_key(session):
        return (
            session.get("updated_at") or "",
            session.get("created_at") or "",
            session.get("id") or 0,
        )

    sessions.sort(key=sort_key, reverse=True)
    if current_session is None:
        return -1
    try:
        return sessions.index(current_session)
    except ValueError:
        return -1


def persist_session_update(sessions, index, history, active_model, active_backend, db_path):
    if index < 0 or index >= len(sessions):
        return -1

    sessions[index]["history"] = history
    sessions[index]["model"] = active_model
    sessions[index]["backend"] = active_backend

    if history:
        first_user_message = next(
            (
                msg.get("content", "").strip()
                for msg in history
                if msg.get("role") == "user" and msg.get("content")
            ),
            "",
        )
        if first_user_message:
            now = datetime.now()
            base_label = first_user_message[:30] + "..." if len(first_user_message) > 30 else first_user_message
            current_label = sessions[index].get("label", "")
            if _is_default_session_label(current_label):
                sessions[index]["label"] = _label_with_timestamp(base_label, now)
            else:
                sessions[index]["label"] = _label_with_timestamp(current_label, now)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if sessions[index].get("id") is not None:
        session_id = sessions[index]["id"]
        cursor.execute(
            """
            UPDATE sessions
            SET label = ?, model = ?, backend = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (sessions[index]["label"], active_model, active_backend, session_id),
        )
    else:
        cursor.execute(
            """
            INSERT INTO sessions (label, model, backend)
            VALUES (?, ?, ?)
            """,
            (sessions[index]["label"], active_model, active_backend),
        )
        session_id = cursor.lastrowid
        sessions[index]["id"] = session_id

    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

    for msg in history:
        images = None
        if msg.get("images"):
            try:
                image_list = [
                    base64.b64encode(img).decode("utf-8") if isinstance(img, bytes) else img
                    for img in msg["images"]
                ]
                images = json.dumps(image_list)
            except Exception:
                pass
        cursor.execute(
            """
            INSERT INTO messages (session_id, role, content, images)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, msg["role"], msg["content"], images),
        )

    conn.commit()
    conn.close()

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    if not sessions[index].get("created_at"):
        sessions[index]["created_at"] = now_str
    sessions[index]["updated_at"] = now_str

    current_session = sessions[index]
    return sort_sessions(sessions, current_session)


def clear_history_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET is_deleted = 1")
    conn.commit()
    conn.close()


def rename_session(sessions, idx, new_label, db_path):
    if idx < 0 or idx >= len(sessions):
        return False

    label = (new_label or "").strip()
    if not label:
        return False

    session = sessions[idx]
    old_label = session.get("label", "")
    if LABEL_TIMESTAMP_RE.search(old_label):
        label = _label_with_timestamp(label)

    session["label"] = label
    if session.get("id") is not None:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET label = ? WHERE id = ?", (label, session["id"]))
        conn.commit()
        conn.close()
    return True


def delete_session(sessions, idx, db_path):
    if idx < 0 or idx >= len(sessions):
        return None

    session = sessions[idx]
    if session.get("id") is not None:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session["id"],),
        )
        conn.commit()
        conn.close()

    del sessions[idx]
    if not sessions:
        return {"new_index": -1, "session": None}

    new_idx = min(idx, len(sessions) - 1)
    return {"new_index": new_idx, "session": sessions[new_idx]}
