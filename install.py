#!/usr/bin/env python3
"""Installation utilisateur, sans sudo ni modification du profil shell."""
import os
import shutil
from pathlib import Path

FILES = ['main.py', 'brain.py', 'memory.py', 'tools.py', 'config.py',
         'runner.py', 'projects.py', 'codework.py', 'assistant_tools.py', 'ia-lex', 'bonjour', 'README.md', 'requirements.txt']


def install(home=None):
    home = Path(home) if home is not None else Path.home()
    source = Path(__file__).resolve().parent
    app = home / '.local/share/ia-lex/app'
    bindir = home / '.local/bin'
    # Vérifie les collisions avant d'écrire : pas de remplacement d'un autre outil.
    for name in ('ia-lex', 'bonjour'):
        link = bindir / name
        if (link.exists() or link.is_symlink()) and not (link.is_symlink() and link.resolve() == (app / name).resolve()):
            raise FileExistsError(f'{link} existe déjà ; choisis un autre nom ou déplace ce fichier.')
    app.mkdir(parents=True, exist_ok=True)
    bindir.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copy2(source / name, app / name)
    for name in ('ia-lex', 'bonjour'):
        (app / name).chmod(0o755)
        link = bindir / name
        if not link.is_symlink():
            link.symlink_to(app / name)
    print('Installation terminée. Lance : ia-lex ou bonjour ia-lex')
    if str(bindir) not in os.get_exec_path():
        print('Pour ce terminal : export PATH="$HOME/.local/bin:$PATH"')
        print('Pour les prochains terminaux, ajoute cette ligne à ~/.zshrc (Kali) ou ~/.bashrc (Ubuntu).')


if __name__ == '__main__':
    try:
        install()
    except OSError as error:
        raise SystemExit(f'Installation impossible : {error}')
