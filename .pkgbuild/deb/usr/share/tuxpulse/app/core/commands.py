import shutil


def _base_actions():
    actions = []
    if shutil.which('apt'):
        actions.extend([
            {
                'label_en': 'Update package lists',
                'label_ro': 'Actualizează listele de pachete',
                'description_en': 'Runs apt-get update.',
                'description_ro': 'Rulează apt-get update.',
                'commands': [['apt-get', 'update']],
                'root': True,
            },
            {
                'label_en': 'Upgrade packages',
                'label_ro': 'Actualizează pachetele',
                'description_en': 'Runs apt-get upgrade.',
                'description_ro': 'Rulează apt-get upgrade.',
                'commands': [['apt-get', 'upgrade', '-y']],
                'root': True,
            },
            {
                'label_en': 'Autoremove packages',
                'label_ro': 'Elimină pachetele nefolosite',
                'description_en': 'Runs apt-get autoremove.',
                'description_ro': 'Rulează apt-get autoremove.',
                'commands': [['apt-get', 'autoremove', '-y']],
                'root': True,
            },
            {
                'label_en': 'Autoclean',
                'label_ro': 'Elimină fișierele nefolosite din cache',
                'description_en': 'Runs apt-get autoclean.',
                'description_ro': 'Rulează apt-get autoclean.',
                'commands': [['apt-get', 'autoclean']],
                'root': True,
            },
            {
                'label_en': 'Autopurge',
                'label_ro': 'Elimină pachetele vechi și fișierele de configurare',
                'description_en': 'Runs apt-get autopurge.',
                'description_ro': 'Rulează apt-get autopurge.',
                'commands': [['apt-get', 'autopurge', '-y']],
                'root': True,
            },
        ])
    elif shutil.which('dnf'):
        actions.extend([
            {
                'label_en': 'Upgrade packages',
                'label_ro': 'Actualizează pachetele',
                'description_en': 'Runs dnf upgrade.',
                'description_ro': 'Rulează dnf upgrade.',
                'commands': [['dnf', 'upgrade', '-y']],
                'root': True,
            },
        ])
    elif shutil.which('pacman'):
        actions.extend([
            {
                'label_en': 'Sync and upgrade packages',
                'label_ro': 'Sincronizează și actualizează pachetele',
                'description_en': 'Runs pacman -Syu.',
                'description_ro': 'Rulează pacman -Syu.',
                'commands': [['pacman', '-Syu', '--noconfirm']],
                'root': True,
            },
        ])
    elif shutil.which('zypper'):
        actions.extend([
            {
                'label_en': 'Upgrade packages',
                'label_ro': 'Actualizează pachetele',
                'description_en': 'Runs zypper update.',
                'description_ro': 'Rulează zypper update.',
                'commands': [['zypper', '--non-interactive', 'update']],
                'root': True,
            },
        ])

    if shutil.which('flatpak'):
        actions.append({
            'label_en': 'Update Flatpak',
            'label_ro': 'Actualizează Flatpak',
            'description_en': 'Runs flatpak update.',
            'description_ro': 'Rulează flatpak update.',
            'commands': [['flatpak', 'update', '-y']],
            'root': False,
        })
    return actions


def build_actions():
    return _base_actions()