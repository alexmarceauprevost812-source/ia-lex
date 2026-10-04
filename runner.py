"""Exécution bornée, sans shell implicite, après confirmation explicite."""
import os
import selectors
import shlex
import shutil
import signal
import subprocess
import time
from pathlib import Path

from config import COMMAND_TIMEOUT, OUTPUT_LIMIT


def installed_tools():
    found = set()
    for directory in os.get_exec_path():
        try:
            for entry in Path(directory or '.').iterdir():
                if entry.is_file() and os.access(entry, os.X_OK) and entry.name.isprintable():
                    found.add(entry.name)
        except OSError:
            continue
    return sorted(found)


def command_text(argv):
    return shlex.join(argv)


def resolve_command(argv):
    if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or any(ord(c) < 32 or ord(c) == 127 for c in arg) for arg in argv):
        raise ValueError('Commande invalide')
    executable = shutil.which(argv[0])
    if executable is None:
        raise ValueError(f'Programme introuvable : {argv[0]}')
    return [executable] + argv[1:]


def confirm(argv, ask=input):
    # Pas de confirmation implicite par pipe ou fichier.
    import sys
    if not sys.stdin.isatty():
        return False
    return ask(f"Exécuter {command_text(argv)} ? Écris OUI : ").strip() == 'OUI'


def run_command(argv, timeout=COMMAND_TIMEOUT, limit=OUTPUT_LIMIT):
    """L'appelant doit obtenir une confirmation avant cet appel."""
    process = subprocess.Popen(resolve_command(argv), stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               start_new_session=True)
    chunks = bytearray()
    reason = ''
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                reason = 'Délai dépassé'
                break
            for key, _ in selector.select(min(remaining, 0.1)):
                block = os.read(key.fileobj.fileno(), 4096)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                chunks.extend(block[:max(0, limit - len(chunks))])
                if len(chunks) >= limit:
                    reason = 'Limite de sortie atteinte'
                    break
            if reason:
                break
        if not reason:
            try:
                process.wait(timeout=max(0.01, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                reason = 'Délai dépassé'
    except KeyboardInterrupt:
        reason = 'Interrompu par utilisateur'
    finally:
        # Supprime aussi les descendants restés actifs dans le groupe.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        selector.close()
        process.stdout.close()
    return {'code': process.returncode, 'output': chunks.decode('utf-8', errors='replace'), 'reason': reason}


def export_script(commands, target):
    """Script Python autonome : confirmation à chaque commande, arrêt sur erreur."""
    import json
    path = Path(target).expanduser()
    source = Path(__file__).read_text(encoding='utf-8').split('\ndef export_script(', 1)[0]
    source = source.replace('from config import COMMAND_TIMEOUT, OUTPUT_LIMIT',
                            f'COMMAND_TIMEOUT = {COMMAND_TIMEOUT}\nOUTPUT_LIMIT = {OUTPUT_LIMIT}')
    plan = json.dumps(commands, ensure_ascii=True)
    footer = '\n\nPLAN = ' + repr(plan) + '''
if __name__ == '__main__':
    import json
    for step in json.loads(PLAN):
        print(step['explanation'])
        print('Dossier :', os.getcwd())
        if not confirm(step['argv']):
            print('Annulé.')
            break
        result = run_command(step['argv'])
        print(''.join(c if c.isprintable() or c == '\\n' else '?' for c in result['output']))
        print('Code :', result['code'], result['reason'])
        if result['code'] != 0 or result['reason']:
            raise SystemExit(1)
'''
    with path.open('x', encoding='utf-8') as handle:
        handle.write('#!/usr/bin/env python3\n' + source + footer)
    return path.resolve()
