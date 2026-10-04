"""Point d’entrée de IA-LEX Personal V1."""
import json
import sys

from brain import LocalBrain
from config import APP_NAME, MEMORY_PATH, VERSION
from memory import Memory
from tools import clear_screen, say, style, system_info

HELP = """/help   : afficher cette aide
/memory : afficher les échanges enregistrés
/system : afficher les informations système
/clear  : effacer l’écran (conserve la mémoire)
/quit   : quitter
Écris un message pour discuter avec le moteur local."""


def main():
    try:
        memory = Memory(MEMORY_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        say(f"Impossible de charger la mémoire : {error}. Le fichier est conservé. Vérifie-le ou choisis IA_LEX_MEMORY_PATH.")
        return 1
    brain = LocalBrain()
    print(style(f"╔════════════════════════════════╗\n║        {APP_NAME} PERSONAL V{VERSION}     ║\n╚════════════════════════════════╝"))
    say("Bonjour ! Je suis prêt. /help pour commencer.")
    while True:
        try:
            text = input(style("TOI > ", "orange")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            say("À bientôt !")
            return 0
        if not text:
            continue
        command = text.casefold()
        if command == "/quit":
            say("À bientôt !")
            return 0
        if command == "/help":
            say(HELP)
        elif command == "/memory":
            say("\n".join(f"{item['role']} : {item['content']}" for item in memory.messages) or "Mémoire vide.")
        elif command == "/system":
            say(system_info())
        elif command == "/clear":
            clear_screen()
        elif text.startswith("/"):
            say("Commande inconnue. Utilise /help.")
        else:
            answer = brain.reply(text, memory.messages)
            say(answer)
            try:
                memory.add_exchange(text, answer)
            except OSError as error:
                say(f"Échange non enregistré : {error}")


if __name__ == "__main__":
    sys.exit(main())
