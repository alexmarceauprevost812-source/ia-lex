"""Mémoire JSON persistante, écrite atomiquement avec accès privé."""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from config import MAX_MESSAGES


class Memory:
    def __init__(self, path):
        self.path = Path(path)
        self.messages = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, list) or any(
                not isinstance(item, dict)
                or item.get("role") not in ("user", "assistant")
                or not isinstance(item.get("content"), str)
                or not isinstance(item.get("timestamp"), str)
                for item in data
            ):
                raise ValueError("Format de mémoire invalide")
            self.messages = data[-MAX_MESSAGES:]

    def add_exchange(self, question, answer):
        now = datetime.now(timezone.utc).isoformat()
        updated = (self.messages + [
            {"role": "user", "content": question, "timestamp": now},
            {"role": "assistant", "content": answer, "timestamp": now},
        ])[-MAX_MESSAGES:]
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
                name = handle.name
                json.dump(updated, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
            self.messages = updated
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
