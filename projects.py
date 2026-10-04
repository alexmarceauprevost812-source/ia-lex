"""Sauvegardes locales des tâches, sans exécution lors de la reprise."""
import json
import os
import re
import tempfile
from pathlib import Path

from brain import validate_reply


class Projects:
    def __init__(self, directory):
        self.directory = Path(directory)

    def path(self, name):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name):
            raise ValueError('Nom de projet : 1 à 64 lettres, chiffres, tirets ou underscores.')
        return self.directory / (name + '.json')

    def list(self):
        return sorted(p.stem for p in self.directory.glob('*.json'))

    def save(self, name, state):
        target = self.path(name)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.directory, delete=False) as handle:
                temporary = handle.name
                json.dump(state, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def load(self, name):
        state = json.loads(self.path(name).read_text(encoding='utf-8'))
        if not isinstance(state, dict) or not isinstance(state.get('cwd'), str) or not isinstance(state.get('goal'), str):
            raise ValueError('Projet invalide.')
        validate_reply({'answer': state['goal'], 'commands': state.get('pending')})
        if not isinstance(state.get('completed'), list) or any(not isinstance(x, str) for x in state['completed']):
            raise ValueError('Résultats du projet invalides.')
        messages = state.get('messages')
        if not isinstance(messages, list) or any(not isinstance(x, dict) or x.get('role') not in ('user', 'assistant') or not isinstance(x.get('content'), str) or not isinstance(x.get('timestamp'), str) for x in messages):
            raise ValueError('Historique du projet invalide.')
        if not Path(state['cwd']).is_dir():
            raise ValueError('Le dossier du projet n’existe plus.')
        return state
