# IA-LEX Personal V2.1

Assistant Python pour Kali/Ubuntu : conversation avec Ollama local, détection des
outils installés, propositions de commandes, exécution après confirmation et
création de scripts Python. Sans clé API et sans bibliothèque Python externe.
Python 3.8+ et Linux requis.

## Installer et lancer

```bash
git clone -b main https://github.com/alexmarceauprevost812-source/ia-lex.git
cd ia-lex
python3 install.py
export PATH="$HOME/.local/bin:$PATH"
bonjour ia-lex
```

Tu peux aussi lancer `ia-lex`, `./ia-lex` dans le dépôt, ou `python3 main.py`.
L'installation copie l'application dans `~/.local/share/ia-lex/app` et crée deux
raccourcis dans `~/.local/bin`, sans sudo. Elle peut être relancée pour mettre à
jour la copie après `git pull`. Elle refuse de remplacer un autre outil déjà nommé
`bonjour` ou `ia-lex`. La mémoire est conservée lors des mises à jour.
Pour conserver le PATH, ajoute `export PATH="$HOME/.local/bin:$PATH"` à
`~/.zshrc` sur Kali ou `~/.bashrc` sur Ubuntu, puis ouvre un nouveau terminal.

## Ajouter l'IA locale Ollama

Installe Ollama avec les instructions officielles : https://ollama.com/download/linux
Puis, dans un terminal :

```bash
ollama serve
```

Si Ollama tourne déjà comme service, inutile de relancer le serveur.
Dans un autre terminal, télécharge un modèle local puis lance IA-LEX :

```bash
ollama pull qwen2.5:7b
bonjour ia-lex
```

Le téléchargement exige une connexion ; l'utilisation du modèle local fonctionne
ensuite hors ligne. La vitesse et la mémoire requise dépendent du modèle et du PC.
Pour utiliser un autre modèle déjà téléchargé :

```bash
IA_LEX_MODEL=qwen2.5:3b ia-lex
```

L'API utilise `http://127.0.0.1:11434/api/chat` avec un schéma JSON, selon
https://docs.ollama.com/api/chat et https://docs.ollama.com/capabilities/structured-outputs.
`IA_LEX_OLLAMA_URL` permet de changer le port local ; seuls les hôtes de boucle
locale HTTP sont acceptés. Aucun envoi direct vers une API distante.
Sans Ollama, les commandes locales restent disponibles et un message explique
comment lancer le serveur lors d'une demande de conversation.

## Utilisation

```text
TOI > quels outils réseau sont installés ?
TOI > /tools nmap
TOI > explique mes interfaces réseau et propose une commande
IA-LEX > ... proposition et explication ...
TOI > /run
Exécuter /usr/sbin/ip addr ? Écris OUI : OUI
IA-LEX > ... résultat puis explication par Ollama ...
```

L'exemple est indicatif : les réponses dépendent du modèle. IA-LEX repère les
exécutables du PATH, y compris les outils Kali présents. Il n'installe pas tous les
outils Kali et ne garantit pas de connaître toutes leurs options. Demande des
précisions quand une proposition ne correspond pas à ton objectif.

| Commande | Action |
| --- | --- |
| `/help` | Aide |
| `/memory` | Historique persistant |
| `/system` | Système, Python et dossier de travail |
| `/tools [filtre]` | Inventaire des programmes installés |
| `/plan` | Commandes en attente et explications |
| `/run` | Exécuter une étape après confirmation exacte `OUI` |
| `/cancel` | Annuler le plan |
| `/cd chemin` | Changer le dossier ; annuler l'ancien plan |
| `/script chemin.py` | Exporter le plan vers un nouveau script |
| `/clear` | Effacer l'écran, conserver la mémoire |
| `/quit` | Quitter ; Ctrl+C et Ctrl+D fonctionnent aussi |

Après chaque résultat, l'utilisateur peut demander une explication ou corriger le
plan. Après la dernière étape, demande une analyse à Ollama pour obtenir une suite ;
toute nouvelle exécution exige encore `/run` et `OUI`.
Une erreur ou interruption arrête le plan. Une nouvelle demande remplace le plan.

## Automatiser un plan

Demande par exemple : « prépare un plan pour inventorier mon système ».
Consulte `/plan`, puis `/script inventaire.py` pour créer un script Python autonome.
Lance-le avec `python3 inventaire.py`. Chaque commande exige encore `OUI` ; le
script s'arrête si une commande échoue. Un fichier existant n'est jamais écrasé.

Les commandes s'exécutent dans le dossier affiché, avec tes droits actuels, sans
shell implicite : `|`, `>`, `&&` et les variables ne sont pas interprétés.
Les programmes interactifs et les demandes de mot de passe ne sont pas pris en
charge (entrée standard fermée). Pour `sudo`, utilise ton terminal directement.
Chaque processus est limité à 60 secondes et 16 000 octets de sortie ; atteindre
une limite arrête le groupe de processus. Les programmes peuvent modifier tes
fichiers ou ton réseau : lis la commande exacte avant de confirmer. Ce n'est pas
un bac à sable. Utilise les outils de sécurité sur tes systèmes ou ceux autorisés.
Il n'y a pas de mode d'exécution automatique sans confirmation.

## Mémoire et apparence

200 derniers messages stockés en clair dans `~/.local/share/ia-lex/memory.json`,
avec écriture atomique et permissions 600. Les sorties exécutées sont enregistrées
et transmises au modèle Ollama configuré pour les analyser. Les 20 derniers
messages, tronqués à 12 000 caractères chacun, fournissent le contexte au modèle.
Ne fournis pas de mots de passe. Un fichier JSON invalide bloque le lancement et
reste intact. Quitte l'application puis supprime le fichier pour oublier l'historique.
`IA_LEX_MEMORY_PATH` change l'emplacement. Le plan en attente n'est pas restauré.

Vert lime et orange sur le fond du terminal ; choisis un fond noir dans ton terminal.
`NO_COLOR=1` désactive les couleurs. Elles sont aussi désactivées hors terminal.
Les confirmations d'exécution sont refusées lorsque l'entrée est redirigée.

## Architecture et vérification

- `main.py` : conversation, commandes et confirmations.
- `brain.py` : client Ollama et validation stricte des propositions.
- `runner.py` : inventaire, processus bornés et scripts.
- `memory.py` : mémoire JSON ; `tools.py` : affichage ; `config.py` : paramètres.
- `install.py`, `ia-lex`, `bonjour` : installation et lancement simple.

```bash
python3 -m unittest discover -s tests -v
```

Les tests simulent l'API Ollama, vérifient les confirmations, la mémoire, les limites,
les scripts et l'installation. Ils ne téléchargent pas de modèle Ollama.

## Terminal V2.1 : diagnostic, guide et projets

Le bandeau affiche **IA-L** en orange foncé et **EX** en blanc. Tout reste dans le
terminal, y compris les explications, résultats et validations.

- `/diagnostic` prépare un plan : système, disque, RAM, interfaces et services en
  échec, selon les programmes présents. Il ne lance aucun contrôle : utilise
  `/run` puis `OUI` pour chaque commande.
- `/guide nmap` explique l'outil et propose de lire son manuel installé, toujours
  après validation. Un petit catalogue décrit les outils courants ; les autres
  programmes du PATH utilisent leur manuel. Sans `man`, demande à Ollama.
- `/plan` affiche l'objectif, les étapes restantes et les codes de résultat.
- `/project save mon-pc` sauvegarde le dossier, l'objectif, les commandes restantes,
  les résultats et l'historique. Réutiliser le nom remplace cette sauvegarde.
- `/project list` liste les sauvegardes ; `/project load mon-pc` reprend une tâche
  sans exécuter de commande. Relis le plan car l'état du PC peut avoir changé.

Les projets sont des JSON privés, en clair, dans un dossier `projects` voisin du
fichier de mémoire. Ils contiennent aussi les sorties dans l'historique. La reprise
remplace le contexte de conversation en cours ; sauvegarde ton projet avant d'en
charger un autre. Les sauvegardes sont manuelles. Un changement de dossier avec
`/cd` annule les commandes en attente.
