"""Exécution bornée, sans shell implicite, après confirmation explicite."""
import os
import queue
import threading
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
    return subprocess.list2cmdline(argv) if os.name == 'nt' else shlex.join(argv)


def split_input(text):
    if os.name != 'nt':
        return shlex.split(text)
    if not text.strip():
        return []
    import ctypes
    from ctypes import wintypes
    parser = ctypes.windll.shell32.CommandLineToArgvW
    parser.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    parser.restype = ctypes.POINTER(wintypes.LPWSTR)
    count = ctypes.c_int()
    pointer = parser('ia-lex ' + text, ctypes.byref(count))
    if not pointer:
        raise ValueError('Arguments Windows invalides.')
    try:
        return [pointer[index] for index in range(1, count.value)]
    finally:
        free = ctypes.windll.kernel32.LocalFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = ctypes.c_void_p
        free(pointer)


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
    windows = os.name == 'nt'
    options = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if windows else {'start_new_session': True}
    process = subprocess.Popen(resolve_command(argv), stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **options)
    chunks = bytearray()
    reason = ''
    output = queue.Queue(maxsize=8)
    stop = threading.Event()

    def send(block):
        while not stop.is_set():
            try:
                output.put(block, timeout=.1)
                return
            except queue.Full:
                pass

    def reader():
        try:
            while not stop.is_set():
                block = os.read(process.stdout.fileno(), 4096)
                if not block:
                    break
                send(block)
        except OSError:
            pass
        finally:
            send(None)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    deadline = time.monotonic() + timeout
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                reason = 'Délai dépassé'
                break
            try:
                block = output.get(timeout=min(remaining, .1))
            except queue.Empty:
                continue
            if block is None:
                break
            chunks.extend(block[:max(0, limit - len(chunks))])
            if len(chunks) >= limit:
                reason = 'Limite de sortie atteinte'
                break
        if not reason:
            try:
                process.wait(timeout=max(.01, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                reason = 'Délai dépassé'
    except KeyboardInterrupt:
        reason = 'Interrompu par utilisateur'
    finally:
        stop.set()
        if windows:
            if process.poll() is None or reason:
                try:
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            if process.poll() is None:
                process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait()
        thread.join(timeout=1)
        if not thread.is_alive():
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
