import shutil
import subprocess
from copy import deepcopy
from functools import lru_cache
from typing import Dict, List

from core.helper_client import helper_available, send_request
from core.pkg_backend import PackageBackend
from core.privilege import elevated_command
from services.apps_catalog import APPS

_backend = PackageBackend()


def get_categories() -> Dict[str, List[dict]]:
    return deepcopy(APPS)


def _native_package_for(app: dict) -> str:
    return app.get("packages", {}).get(_backend.pm, "")


@lru_cache(maxsize=512)
def native_package_available(pkg_name: str) -> bool:
    if not pkg_name:
        return False
    try:
        if _backend.pm == "apt":
            proc = subprocess.run(["apt-cache", "show", pkg_name], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            return proc.returncode == 0 and bool(proc.stdout.strip())
        if _backend.pm == "pacman":
            proc = subprocess.run(["pacman", "-Si", pkg_name], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            return proc.returncode == 0
        if _backend.pm == "dnf":
            proc = subprocess.run(["dnf", "info", pkg_name], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            return proc.returncode == 0
        if _backend.pm == "zypper":
            proc = subprocess.run(["zypper", "--non-interactive", "info", pkg_name], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            return proc.returncode == 0 and "Information for package" in proc.stdout
    except Exception:
        return False
    return False


def is_installed(pkg_name: str) -> bool:
    if not pkg_name:
        return False
    try:
        if _backend.pm == "apt":
            subprocess.check_output(["dpkg", "-s", pkg_name], stderr=subprocess.DEVNULL)
        elif _backend.pm == "pacman":
            subprocess.check_output(["pacman", "-Q", pkg_name], stderr=subprocess.DEVNULL)
        elif _backend.pm in {"dnf", "zypper"}:
            subprocess.check_output(["rpm", "-q", pkg_name], stderr=subprocess.DEVNULL)
        else:
            return False
        return True
    except Exception:
        return False


def is_flatpak_installed(app_id: str) -> bool:
    if not app_id or shutil.which("flatpak") is None:
        return False
    try:
        subprocess.check_output(["flatpak", "info", app_id], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def app_state(app: dict) -> str:
    pkg = _native_package_for(app)
    flatpak_id = app.get("flatpak")
    if pkg and is_installed(pkg):
        return "installed-native"
    if flatpak_id and is_flatpak_installed(flatpak_id):
        return "installed-flatpak"
    return "available"


def apps_for_display(search: str = "") -> Dict[str, List[dict]]:
    needle = (search or "").strip().lower()
    result: Dict[str, List[dict]] = {}
    for category, apps in APPS.items():
        visible = []
        for app in apps:
            enriched = deepcopy(app)
            enriched["native_package"] = _native_package_for(app)
            enriched["native_available"] = native_package_available(enriched["native_package"])
            enriched["flatpak_available"] = bool(app.get("flatpak"))
            enriched["state"] = app_state(app)
            if not enriched["native_available"] and enriched["flatpak_available"]:
                enriched["source"] = "flatpak"
            else:
                enriched["source"] = "native"
            text = " ".join([
                app.get("name", ""),
                app.get("description", ""),
                category,
                enriched.get("native_package", ""),
                app.get("flatpak", "") or "",
            ]).lower()
            if needle and needle not in text:
                continue
            visible.append(enriched)
        if visible:
            result[category] = visible
    return result


def _run_command(cmd: List[str], action: str = "install") -> str:
    if helper_available():
        response = send_request({"action": action, "cmd": cmd})
        if response.get("code", 1) != 0:
            raise RuntimeError(response.get("output", "Operation failed."))
        return response.get("output", "")

    elevated = elevated_command(cmd)
    proc = subprocess.run(elevated, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout.strip() or "Operation failed.")
    return proc.stdout.strip()


def install_native_packages(packages: List[str]) -> str:
    packages = [p for p in packages if p]
    if not packages:
        return ""
    if _backend.pm == "apt":
        cmd = ["apt", "install", "-y"] + packages
    elif _backend.pm == "pacman":
        cmd = ["pacman", "-S", "--noconfirm"] + packages
    elif _backend.pm == "dnf":
        cmd = ["dnf", "install", "-y"] + packages
    elif _backend.pm == "zypper":
        cmd = ["zypper", "--non-interactive", "install"] + packages
    else:
        raise RuntimeError("Unsupported distribution.")
    return _run_command(cmd, action="install")


def remove_native_packages(packages: List[str]) -> str:
    packages = [p for p in packages if p]
    if not packages:
        return ""
    if _backend.pm == "apt":
        cmd = ["apt", "remove", "-y"] + packages
    elif _backend.pm == "pacman":
        cmd = ["pacman", "-R", "--noconfirm"] + packages
    elif _backend.pm == "dnf":
        cmd = ["dnf", "remove", "-y"] + packages
    elif _backend.pm == "zypper":
        cmd = ["zypper", "--non-interactive", "remove"] + packages
    else:
        raise RuntimeError("Unsupported distribution.")
    return _run_command(cmd, action="remove")


def update_native_packages(packages: List[str]) -> str:
    packages = [p for p in packages if p]
    if not packages:
        return ""
    if _backend.pm == "apt":
        cmd = ["apt", "install", "-y"] + packages
    elif _backend.pm == "pacman":
        cmd = ["pacman", "-S", "--noconfirm"] + packages
    elif _backend.pm == "dnf":
        cmd = ["dnf", "upgrade", "-y"] + packages
    elif _backend.pm == "zypper":
        cmd = ["zypper", "--non-interactive", "update"] + packages
    else:
        raise RuntimeError("Unsupported distribution.")
    return _run_command(cmd, action="update")


def install_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")
    output_parts = []
    for app_id in [a for a in app_ids if a]:
        output_parts.append(_run_command(["flatpak", "install", "-y", "flathub", app_id], action="install"))
    return "\n".join(part for part in output_parts if part)


def remove_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")
    output_parts = []
    for app_id in [a for a in app_ids if a]:
        output_parts.append(_run_command(["flatpak", "uninstall", "-y", app_id], action="remove"))
    return "\n".join(part for part in output_parts if part)


def update_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")
    output_parts = []
    for app_id in [a for a in app_ids if a]:
        output_parts.append(_run_command(["flatpak", "update", "-y", app_id], action="update"))
    return "\n".join(part for part in output_parts if part)


def _collect(selection: List[dict], mode: str) -> tuple[list[str], list[str]]:
    native_packages: List[str] = []
    flatpak_ids: List[str] = []

    for app in selection:
        source = app.get("source", "native")
        state = app_state(app)
        native_pkg = app.get("native_package") or _native_package_for(app)
        flatpak_id = app.get("flatpak")
        native_available = native_package_available(native_pkg)

        if mode == "install":
            if source == "flatpak":
                if flatpak_id and not is_flatpak_installed(flatpak_id):
                    flatpak_ids.append(flatpak_id)
            else:
                if native_pkg and native_available and not is_installed(native_pkg):
                    native_packages.append(native_pkg)
                elif flatpak_id and not is_flatpak_installed(flatpak_id):
                    flatpak_ids.append(flatpak_id)

        elif mode == "remove":
            if state == "installed-flatpak" and flatpak_id:
                flatpak_ids.append(flatpak_id)
            elif state == "installed-native" and native_pkg:
                native_packages.append(native_pkg)

        elif mode == "update":
            if state == "installed-flatpak" and flatpak_id:
                flatpak_ids.append(flatpak_id)
            elif state == "installed-native" and native_pkg:
                native_packages.append(native_pkg)

    return native_packages, flatpak_ids


def install_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids = _collect(selection, "install")
    outputs = []
    if native_packages:
        outputs.append(install_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(install_flatpak_apps(flatpak_ids))
    return "\n\n".join(part for part in outputs if part).strip() or "Nothing to install."


def remove_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids = _collect(selection, "remove")
    outputs = []
    if native_packages:
        outputs.append(remove_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(remove_flatpak_apps(flatpak_ids))
    return "\n\n".join(part for part in outputs if part).strip() or "Nothing to remove."


def update_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids = _collect(selection, "update")
    outputs = []
    if native_packages:
        outputs.append(update_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(update_flatpak_apps(flatpak_ids))
    return "\n\n".join(part for part in outputs if part).strip() or "Nothing to update."
