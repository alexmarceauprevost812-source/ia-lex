"""Configuration locale, sans secrets ni dépendances externes."""
import os
from pathlib import Path

APP_NAME = "IA-LEX"
VERSION = "1.0"
MEMORY_PATH = Path(os.environ.get("IA_LEX_MEMORY_PATH", "~/.local/share/ia-lex/memory.json")).expanduser()
MAX_MESSAGES = 200
