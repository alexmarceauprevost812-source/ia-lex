# IA-LEX Personal V1

Assistant personnel en Python pour Kali Linux et Ubuntu. Fonctionne hors ligne,
sans clé API, sans service externe et sans dépendance à installer.
La V1 utilise un moteur à règles simples : ce n’est pas encore un modèle de langage.

## Lancement

Python 3.8 ou plus récent est requis. Si Python manque :

```bash
sudo apt update
sudo apt install python3
```

```bash
git clone https://github.com/alexmarceauprevost812-source/ti-lex-ia-.git
cd ti-lex-ia-
git switch main
python3 main.py
```

## Commandes

| Commande | Action |
| --- | --- |
| `/help` | Afficher l’aide |
| `/memory` | Afficher les échanges enregistrés |
| `/system` | Afficher le système, l’architecture et Python |
| `/clear` | Effacer l’écran, conserver la mémoire |
| `/quit` | Quitter proprement |

Ctrl+C et Ctrl+D quittent également. Essaie `bonjour`, `qui es-tu ?`, puis
`tu te souviens de mon dernier message ?`. Les commandes ne sont pas enregistrées.

## Mémoire et confidentialité

Les 200 derniers messages (100 échanges) sont stockés en JSON dans
`~/.local/share/ia-lex/memory.json`, avec écriture atomique et permissions privées
du fichier (600 sous Linux). La mémoire est en clair, sans chiffrement.
Pour la supprimer, quitte le programme puis supprime ce fichier.
Un fichier invalide est conservé et bloque le lancement pour éviter sa perte.
Pour choisir un autre emplacement :

```bash
IA_LEX_MEMORY_PATH=/tmp/ia-lex-demo.json python3 main.py
```

## Apparence

Vert lime pour IA-LEX, orange pour le prompt utilisateur, sur le fond du terminal.
Choisis un fond noir dans ton terminal. Les couleurs sont désactivées quand la
sortie est redirigée, avec `TERM=dumb`, ou avec `NO_COLOR=1`.

## Architecture et extension Ollama

- `main.py` : boucle terminal et commandes.
- `brain.py` : contrat `Brain.reply(text, history)` et moteur local.
- `memory.py` : historique JSON persistant.
- `tools.py` : affichage et informations système.
- `config.py` : nom, version, chemin de mémoire et limite d’historique.

Pour une future intégration Ollama, implémente un moteur avec le même contrat
`reply`, puis remplace `LocalBrain()` dans `main.py`. L’historique est transmis
avant l’enregistrement du nouvel échange. Prévoir les délais, les erreurs de
connexion et le modèle choisi. Aucun appel Ollama n’est effectué dans cette V1.
IA-LEX n’exécute aucune commande shell issue des messages.
