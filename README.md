# IA-LEX Personal V2.5

Assistant Python pour Windows, Kali et Ubuntu : conversation avec Ollama local, détection des
outils installés, propositions de commandes, exécution après confirmation et
création de scripts Python. Sans clé API et sans bibliothèque Python externe.
Python 3.8+ requis. Windows 10/11, Kali et Ubuntu pris en charge.

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

## V2.2 : aide au code dans le terminal

Tu peux demander à Ollama de créer du Python, HTML/CSS, JavaScript ou du Bash,
expliquer du code et proposer des corrections. La qualité dépend du modèle local.

```text
/cd /home/ton-compte/mes-projets
/tree
Crée un petit projet Python dans factures avec un README et un programme de calcul.
/diff
/apply
```

`/apply` affiche les différences puis exige `OUI` pour **un seul fichier**. Répète
la commande pour chaque fichier. Les dossiers parents sont créés avec le fichier,
après validation. Les tests et autres commandes proposées attendent ensuite `/run`
et leur propre `OUI`. Aucun code généré n'est exécuté lors de l'enregistrement.

Pour travailler sur un fichier existant : `/read factures/main.py`, puis décris
la modification voulue. `/read` affiche le contenu et le fournit au modèle Ollama
local dans le contexte. `/tree` montre jusqu'à 300 entrées du dossier actuel,
sans parcourir `.git`, `.venv`, `node_modules` ou les liens symboliques.

Les fichiers doivent être en UTF-8, de 64 Ko maximum, avec des chemins relatifs au
dossier choisi par `/cd`. Les liens symboliques et les chemins qui sortent de ce
dossier sont refusés. Les anciennes versions sont conservées dans un dossier
`backups` voisin de la mémoire, avec permissions privées. IA-LEX refuse d'appliquer
une proposition si le fichier a changé depuis sa préparation. `/cancel`, une
nouvelle demande ou un changement de dossier annulent les propositions de fichiers.
Les propositions d'écriture ne sont pas restaurées par `/project load` : demande
une nouvelle proposition après avoir repris le projet. `/script` exporte uniquement
les commandes, pas les modifications de fichiers.

## V2.3 : écriture fluide

Les réponses apparaissent progressivement dès que le modèle Ollama produit du
texte, sans délai artificiel entre les caractères. Les commandes et fichiers sont
validés seulement après réception complète ; une interruption ne crée aucun plan.
La vitesse réelle de génération dépend du modèle, du CPU/GPU et de la RAM. Pour
un modèle plus léger, télécharge `ollama pull qwen2.5:3b`, puis lance
`IA_LEX_MODEL=qwen2.5:3b bonjour ia-lex`.

## V2.4 : voir et lancer les outils du terminal

- `/tools` affiche tous les exécutables trouvés dans ton PATH, sans liste Kali figée.
- `/tools python` filtre les noms ; `/which python3` affiche le chemin exact.
- `/exec python3 --version` prépare ta commande sans Ollama. Utilise ensuite
  `/run` et écris `OUI` pour l'exécuter. Chaque nouvelle commande exige cette validation.

Les guillemets sont pris en charge, par exemple `/exec ls "Mon dossier"`. Il n'y a
pas de shell implicite : pipes, redirections et variables restent littéraux. Les
outils interactifs, graphiques et ceux qui demandent un mot de passe ne sont pas
pris en charge par l'exécution capturée. Les limites de temps et de sortie restent
actives. Les logiciels hors du PATH ne figurent pas dans `/tools` ; un chemin
explicite peut être utilisé avec `/exec`. La commande remplace le plan en attente.

Les commandes proposées et celles affichées avant validation utilisent le vert
lime pour le programme, l'orange foncé pour les options (`--version`, `-h`) et le
blanc pour les autres arguments. `NO_COLOR=1` conserve un affichage sans couleurs.

## V2.5 : assistance aux commandes étape par étape

Décris ton objectif, par exemple `/aide trouver les gros fichiers de ce dossier`.
IA-LEX propose une seule commande à la fois, explique ce qu'elle fait et attend
`/run` puis `OUI`. Après l'exécution, Ollama analyse le résultat et propose la suite
si nécessaire. Une erreur arrête l'ancien plan et déclenche une proposition de
correction. Aucune étape suivante n'est exécutée automatiquement. Le dossier
actuel et l'objectif sont fournis au modèle pour adapter les propositions.
Sans serveur Ollama, la commande exécutée et son résultat restent enregistrés,
mais l'analyse automatique affiche une erreur de connexion.

## Installation Windows 10/11

Installe Python depuis https://www.python.org/downloads/windows/ et Ollama depuis
https://ollama.com/download/windows. Utilise Windows Terminal ou PowerShell.
Télécharge le dépôt (Git ou ZIP), ouvre son dossier et lance :

```powershell
py install.py
```

L'installation affiche la ligne PowerShell exacte à copier pour ajouter les
raccourcis au PATH du terminal. Exécute cette ligne, puis :

```powershell
ollama pull qwen2.5:7b
bonjour ia-lex
```

L'application est copiée dans `%LOCALAPPDATA%/IA-LEX/app` et la mémoire se trouve
à `%LOCALAPPDATA%/IA-LEX/memory.json`. Les fichiers `.cmd` permettent `ia-lex` et
`bonjour ia-lex`, sans droits administrateur. Pour garder ces commandes dans les
futurs terminaux, ajoute le dossier app indiqué au PATH utilisateur Windows.

`/tools` liste les exécutables disponibles dans le PATH Windows ; les commandes
internes de CMD comme `dir` n'y figurent pas. Exemple : `/exec cmd /c dir`, puis
`/run` et `OUI`. `/diagnostic` prépare des lectures via PowerShell. Les programmes
Kali ne sont pas installés sous Windows automatiquement : pour Kali, utilise son
terminal dans WSL et l'installation Linux. IA-LEX communique au modèle le système
réel pour adapter les commandes. Les chemins Windows et les guillemets sont
analysés selon les règles Windows. Les droits privés 600 documentés pour les
sauvegardes concernent Linux ; sous Windows, les droits dépendent de ton compte.

Les tests Windows de cette version vérifient les fichiers d'installation et les
plans PowerShell par simulation. Le lancement réel sous Windows reste à vérifier
sur un PC Windows ; les tests d'exécution ont été réalisés sous Linux.
