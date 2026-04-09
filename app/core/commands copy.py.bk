from __future__ import annotations

import shutil
from typing import Dict, List


def _action(
    *,
    label_en: str,
    label_ro: str,
    description_en: str,
    description_ro: str,
    commands: List[List[str]],
    root: bool,
) -> Dict[str, object]:
    return {
        "label_en": label_en,
        "label_ro": label_ro,
        "description_en": description_en,
        "description_ro": description_ro,
        "commands": commands,
        "root": root,
    }


def _base_actions() -> List[Dict[str, object]]:
    actions: List[Dict[str, object]] = []

    if shutil.which("apt"):
        actions.extend(
            [
                _action(
                    label_en="Update package lists",
                    label_ro="Actualizează listele de pachete",
                    description_en="Runs apt update.",
                    description_ro="Rulează apt update.",
                    commands=[["apt", "update"]],
                    root=True,
                ),
                _action(
                    label_en="Upgrade packages",
                    label_ro="Actualizează pachetele",
                    description_en="Runs apt upgrade.",
                    description_ro="Rulează apt upgrade.",
                    commands=[["apt", "upgrade", "-y"]],
                    root=True,
                ),
                _action(
                    label_en="Autoremove packages",
                    label_ro="Elimină pachetele nefolosite",
                    description_en="Runs apt autoremove.",
                    description_ro="Rulează apt autoremove.",
                    commands=[["apt", "autoremove", "-y"]],
                    root=True,
                ),
                _action(
                    label_en="Autoclean cache",
                    label_ro="Curăță cache-ul apt",
                    description_en="Runs apt autoclean.",
                    description_ro="Rulează apt autoclean.",
                    commands=[["apt", "autoclean", "-y"]],
                    root=True,
                ),
            ]
        )

    elif shutil.which("dnf"):
        actions.extend(
            [
                _action(
                    label_en="Refresh package metadata",
                    label_ro="Actualizează metadata pachetelor",
                    description_en="Runs dnf makecache --refresh.",
                    description_ro="Rulează dnf makecache --refresh.",
                    commands=[["dnf", "makecache", "--refresh", "-y"]],
                    root=True,
                ),
                _action(
                    label_en="Upgrade packages",
                    label_ro="Actualizează pachetele",
                    description_en="Runs dnf upgrade.",
                    description_ro="Rulează dnf upgrade.",
                    commands=[["dnf", "upgrade", "-y"]],
                    root=True,
                ),
                _action(
                    label_en="Autoremove unused dependencies",
                    label_ro="Elimină dependențele nefolosite",
                    description_en="Runs dnf autoremove.",
                    description_ro="Rulează dnf autoremove.",
                    commands=[["dnf", "autoremove", "-y"]],
                    root=True,
                ),
                _action(
                    label_en="Clean DNF cache",
                    label_ro="Curăță cache-ul DNF",
                    description_en="Runs dnf clean all.",
                    description_ro="Rulează dnf clean all.",
                    commands=[["dnf", "clean", "all"]],
                    root=True,
                ),
            ]
        )

    elif shutil.which("pacman"):
        actions.extend(
            [
                _action(
                    label_en="Sync and upgrade packages",
                    label_ro="Sincronizează și actualizează pachetele",
                    description_en="Runs pacman -Syu.",
                    description_ro="Rulează pacman -Syu.",
                    commands=[["pacman", "-Syu", "--noconfirm"]],
                    root=True,
                ),
                _action(
                    label_en="Clean package cache",
                    label_ro="Curăță cache-ul pachetelor",
                    description_en="Runs pacman -Sc.",
                    description_ro="Rulează pacman -Sc.",
                    commands=[["pacman", "-Sc", "--noconfirm"]],
                    root=True,
                ),
            ]
        )

    elif shutil.which("zypper"):
        actions.extend(
            [
                _action(
                    label_en="Refresh repositories",
                    label_ro="Actualizează repository-urile",
                    description_en="Runs zypper refresh.",
                    description_ro="Rulează zypper refresh.",
                    commands=[["zypper", "--non-interactive", "refresh"]],
                    root=True,
                ),
                _action(
                    label_en="Upgrade packages",
                    label_ro="Actualizează pachetele",
                    description_en="Runs zypper update.",
                    description_ro="Rulează zypper update.",
                    commands=[["zypper", "--non-interactive", "update"]],
                    root=True,
                ),
                _action(
                    label_en="Clean zypper cache",
                    label_ro="Curăță cache-ul zypper",
                    description_en="Runs zypper clean.",
                    description_ro="Rulează zypper clean.",
                    commands=[["zypper", "clean", "--all"]],
                    root=True,
                ),
            ]
        )

    if shutil.which("flatpak"):
        actions.append(
            _action(
                label_en="Update Flatpak",
                label_ro="Actualizează Flatpak",
                description_en="Runs flatpak update.",
                description_ro="Rulează flatpak update.",
                commands=[["flatpak", "update", "-y"]],
                root=False,
            )
        )

    return actions


def build_actions():
    return _base_actions()
