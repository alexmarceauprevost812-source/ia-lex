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
    if os.name == 'nt':
        return install_windows(home, source)
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


def install_windows(home, source):
    import sys
    app = Path(os.environ.get('LOCALAPPDATA', str(home / 'AppData/Local'))) / 'IA-LEX' / 'app'
    app.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copy2(source / name, app / name)
    python = sys.executable
    if any(c in str(app) + python for c in ('%', '\n', '\r')):
        raise ValueError('Chemin Windows incompatible avec les raccourcis CMD.')
    for name in ('ia-lex', 'bonjour'):
        check = 'if /I not "%~1"=="ia-lex" (echo Utilisation : bonjour ia-lex & exit /b 2)\n' if name == 'bonjour' else ''
        (app / (name + '.cmd')).write_text('@echo off\n' + check + f'"{python}" "{app / "main.py"}"\n', encoding='utf-8')
    print('Installation terminée. Pour ce terminal PowerShell :')
    print('$env:Path = "' + str(app) + ';" + $env:Path')
    print('Puis lance : bonjour ia-lex')
    print('Pour un lancement permanent, ajoute ce dossier au PATH utilisateur : ' + str(app))


if __name__ == '__main__':
    try:
        install()
    except (OSError, ValueError) as error:
        raise SystemExit(f'Installation impossible : {error}')
