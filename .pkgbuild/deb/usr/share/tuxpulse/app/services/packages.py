from __future__ import annotations

import subprocess

from core.pkg_backend import PackageBackend
from core.privilege import elevated_command


def _backend() -> PackageBackend:
    return PackageBackend()


def list_installed_packages(limit=300, search=""):
    return _backend().list_installed(search=search, limit=limit)


def count_installed_packages():
    return _backend().count_installed()


def list_upgradable_packages(limit=300):
    return _backend().list_upgradable(limit=limit)


def _run_pkg_command(cmd, ok_message):
    try:
        command = elevated_command(cmd)
    except RuntimeError as exc:
        raise RuntimeError(str(exc)) from exc

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or f'Failed to run: {" ".join(command)}')
    return result.stdout.strip() or ok_message


def remove_package(name: str):
    return _run_pkg_command(_backend().remove_cmd(name), f"Package {name} removed.")


def purge_package(name: str):
    return _run_pkg_command(_backend().purge_cmd(name), f"Package {name} purged.")
