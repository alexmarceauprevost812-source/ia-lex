"""Plans de diagnostic et guide local : aucune exécution automatique."""
import shutil
import os

GUIDE = {
    'nmap': 'Inventaire réseau et ports sur les machines autorisées.',
    'wireshark': 'Analyse graphique des captures réseau ; utilise tshark pour le terminal.',
    'tshark': 'Lecture et analyse des captures réseau dans le terminal.',
    'tcpdump': 'Capture et lecture du trafic réseau ; certains usages exigent des privilèges.',
    'ip': 'Interfaces, adresses et routes réseau.',
    'curl': 'Requêtes et transferts HTTP et autres protocoles.',
    'ss': 'Connexions et sockets locales.',
    'nikto': 'Audit de configuration de serveurs web autorisés.',
    'gobuster': 'Recherche de chemins et noms sur des services autorisés.',
    'john': 'Audit de robustesse des mots de passe avec des données autorisées.',
    'hashcat': 'Audit de mots de passe à partir de condensats autorisés.',
    'msfconsole': 'Console Metasploit pour laboratoires et audits autorisés.',
}


def diagnostic_plan():
    if os.name == 'nt':
        executable = shutil.which('powershell.exe') or shutil.which('pwsh')
        checks = [
            'Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,FreePhysicalMemory,TotalVisibleMemorySize',
            'Get-PSDrive -PSProvider FileSystem | Select-Object Name,Used,Free',
            'Get-NetIPConfiguration',
        ]
        return [{'argv': [executable, '-NoProfile', '-NonInteractive', '-Command', command], 'explanation': 'Lire les informations système Windows.'} for command in checks] if executable else []
    checks = [
        (['uname', '-a'], 'Identifier le système et le noyau.'),
        (['df', '-h', '.'], 'Afficher l’espace disque du dossier actuel.'),
        (['free', '-h'], 'Afficher la mémoire RAM disponible.'),
        (['ip', '-brief', 'address'], 'Afficher les interfaces et adresses réseau locales.'),
        (['systemctl', '--failed', '--no-pager'], 'Lister les services en échec si systemd est disponible.'),
    ]
    return [{'argv': argv, 'explanation': explanation} for argv, explanation in checks if shutil.which(argv[0])]


def tool_guide(name, inventory):
    if name not in inventory:
        raise ValueError('Outil absent du PATH. Utilise /tools pour rechercher les noms disponibles.')
    description = GUIDE.get(name, 'Programme installé. Consulte son manuel pour connaître ses fonctions et options exactes.')
    # Le manuel est préféré : certains programmes n’ont pas un --help sans effets.
    commands = [{'argv': ['man', '-P', 'cat', '--', name], 'explanation': 'Lire le manuel installé de cet outil.'}] if shutil.which('man') else []
    return description, commands
