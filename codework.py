"""Lecture locale et modifications proposées, avec aperçu et sauvegarde."""
import difflib
import hashlib
import os
from pathlib import Path
import stat
import tempfile
import uuid

LIMIT = 64000


def target_path(root, relative):
    root = Path(root).resolve()
    path = Path(relative)
    if path.is_absolute() or not path.parts or '..' in path.parts or any(ord(c) < 32 for c in relative):
        raise ValueError('Utilise un chemin relatif dans le dossier de travail.')
    target = root / path
    for parent in [target] + list(target.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError('Les liens symboliques ne sont pas modifiés.')
    target.resolve().relative_to(root)
    return target


def read_file(root, relative):
    target = target_path(root, relative)
    with target.open('rb') as handle:
        raw = handle.read(LIMIT + 1)
    if len(raw) > LIMIT or b'\x00' in raw:
        raise ValueError('Fichier binaire ou trop grand (64 Ko maximum).')
    return raw.decode('utf-8')


def tree(root):
    rows = []
    ignored = {'.git', '.venv', '__pycache__', 'node_modules', '.env'}
    for directory, folders, files in os.walk(root, followlinks=False):
        folders[:] = sorted(name for name in folders if name not in ignored and not Path(directory, name).is_symlink())
        for name in sorted(folders + files):
            if name in ignored or name.startswith('.env.'):
                continue
            path = Path(directory, name)
            rows.append(str(path.relative_to(root)) + ('/' if path.is_dir() else ''))
            if len(rows) >= 300:
                return '\n'.join(rows) + '\n… limite de 300 entrées'
    return '\n'.join(rows) or '(dossier vide)'


def prepare(root, proposal):
    target = target_path(root, proposal['path'])
    before = read_file(root, proposal['path']) if target.exists() else None
    return dict(proposal, root=str(Path(root).resolve()), before=before,
                digest=hashlib.sha256(before.encode()).hexdigest() if before is not None else None)


def preview(edit):
    patch = ''.join(difflib.unified_diff((edit['before'] or '').splitlines(True), edit['content'].splitlines(True),
                                        fromfile=edit['path'] + ' (avant)', tofile=edit['path'] + ' (proposé)'))
    return f"{edit['explanation']}\nDossier : {edit['root']}\nFichier : {edit['path']}\n" + (patch or '(contenu identique)')


def apply(edit, backups):
    target = target_path(edit['root'], edit['path'])
    current = read_file(edit['root'], edit['path']) if target.exists() else None
    if current != edit['before']:
        raise ValueError('Le fichier a changé depuis la proposition. Demande une nouvelle modification.')
    mode = stat.S_IMODE(target.stat().st_mode) if current is not None else 0o644
    backup = None
    if current is not None:
        backups = Path(backups)
        backups.mkdir(parents=True, exist_ok=True, mode=0o700)
        backup = backups / (target.name + '.' + uuid.uuid4().hex + '.bak')
        with backup.open('x', encoding='utf-8') as handle:
            os.chmod(backup, 0o600)
            handle.write(current)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(edit['content'])
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        # Re-vérifie avant la publication ; création exclusive pour un nouveau fichier.
        if (read_file(edit['root'], edit['path']) if target.exists() else None) != current:
            raise ValueError('Le fichier vient de changer. Modification annulée.')
        if current is None:
            os.link(temporary, target)
        else:
            os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return target, backup
