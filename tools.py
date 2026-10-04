"""Affichage terminal et informations système, sans exécution de commandes."""
import os
import platform
import shlex
import sys


def colors_enabled():
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"


def style(text, color="lime"):
    if not colors_enabled():
        return text
    code = {"orange": "38;2;196;81;19", "white": "37", "lime": "38;5;118"}[color]
    return f"\033[{code}m{text}\033[0m"


def safe_text(text):
    # Neutralise les contrôles du terminal provenant des entrées ou du fichier JSON.
    return "".join(c if c.isprintable() or c == "\n" else "?" for c in text)


def say(text):
    print(style("IA-LEX > ") + safe_text(text))


def clear_screen():
    if colors_enabled():
        print("\033[2J\033[H", end="", flush=True)
    else:
        print("Écran effacé (la mémoire est conservée).")


def system_info():
    return f"Système : {platform.system()} {platform.release()}\nArchitecture : {platform.machine()}\nPython : {platform.python_version()}"


def banner(version):
    return style("IA-L", "orange") + style("EX", "white") + f" • PERSONAL V{version} • TERMINAL"


def show_command(argv, label="Commande"):
    """Colorise seulement les arguments assainis, sans interpréter leur contenu."""
    segments = []
    for index, argument in enumerate(argv):
        color = 'lime' if index == 0 else ('orange' if argument.startswith('-') else 'white')
        segments.append(style(safe_text(shlex.quote(argument)), color))
    print(style('IA-LEX > ') + safe_text(label) + ' : ' + ' '.join(segments))
