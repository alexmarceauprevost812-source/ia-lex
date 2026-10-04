"""Configuration locale, sans secrets ni dépendances externes."""
import os
from pathlib import Path

APP_NAME = "IA-LEX"
VERSION = "2.2"
MEMORY_PATH = Path(os.environ.get("IA_LEX_MEMORY_PATH", "~/.local/share/ia-lex/memory.json")).expanduser()
MAX_MESSAGES = 200
OLLAMA_URL = os.environ.get("IA_LEX_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("IA_LEX_MODEL", "qwen2.5:7b")
COMMAND_TIMEOUT = 60
OUTPUT_LIMIT = 16000
