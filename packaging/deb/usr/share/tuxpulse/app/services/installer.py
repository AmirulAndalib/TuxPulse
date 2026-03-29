from __future__ import annotations

import os
import shutil
import subprocess
import unicodedata
from copy import deepcopy
from functools import lru_cache
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from core.helper_client import helper_available, send_request
from core.pkg_backend import PackageBackend
from core.privilege import elevated_command
from services.apps_catalog import APPS

_PACKAGE_BACKEND = PackageBackend()
_SUPPORTED_BACKENDS = ("apt", "pacman", "dnf", "zypper")


# ===============================
# BACKEND DETECTION
# ===============================

def _normalize_backend_name(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if any(token in raw for token in ("apt", "debian", "ubuntu", "nala")):
        return "apt"
    if any(token in raw for token in ("pacman", "arch", "manjaro", "endeavouros")):
        return "pacman"
    if any(token in raw for token in ("dnf", "fedora", "rhel", "rocky", "alma")):
        return "dnf"
    if any(token in raw for token in ("zypper", "opensuse", "suse")):
        return "zypper"
    return raw if raw in _SUPPORTED_BACKENDS else ""


@lru_cache(maxsize=1)
def backend_key() -> str:
    candidates = []
    for attr_name in (
        "name",
        "backend_name",
        "package_manager",
        "manager",
        "current_backend",
        "backend",
        "distro",
    ):
        value = getattr(_PACKAGE_BACKEND, attr_name, None)
        if callable(value):
            try:
                value = value()
            except Exception:
                value = None
        if isinstance(value, str) and value.strip():
            candidates.append(value)

    for candidate in candidates:
        normalized = _normalize_backend_name(candidate)
        if normalized:
            return normalized

    if shutil.which("apt"):
        return "apt"
    if shutil.which("pacman"):
        return "pacman"
    if shutil.which("dnf"):
        return "dnf"
    if shutil.which("zypper"):
        return "zypper"
    return "apt"


# ===============================
# GENERIC HELPERS
# ===============================

def _normalize_text(value: str) -> str:
    cleaned = unicodedata.normalize("NFKD", value or "")
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))
    return cleaned.casefold().strip()


def _deduplicate(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def clear_runtime_caches() -> None:
    backend_key.cache_clear()
    native_package_available.cache_clear()
    is_installed.cache_clear()
    is_flatpak_installed.cache_clear()
    _get_native_upgradable_set.cache_clear()
    _get_flatpak_upgradable_set.cache_clear()


# ===============================
# CATALOG HELPERS
# ===============================

def get_categories() -> Dict[str, List[dict]]:
    return deepcopy(APPS)



def _native_package_for(app: dict, manager: str | None = None) -> str:
    packages = app.get("packages") or {}
    manager = manager or backend_key()
    return (packages.get(manager) or "").strip()



def _preferred_source(native_available: bool, flatpak_available: bool) -> str:
    if native_available:
        return "native"
    if flatpak_available:
        return "flatpak"
    return "native"



def _requested_source(app: dict, native_available: bool, flatpak_available: bool) -> str:
    source = (app.get("source") or "").strip().lower()
    if source == "native" and native_available:
        return "native"
    if source == "flatpak" and flatpak_available:
        return "flatpak"
    if source == "auto":
        return "auto"
    return _preferred_source(native_available, flatpak_available)



def _search_blob(app: dict, category: str, native_package: str) -> str:
    parts = [
        app.get("id", ""),
        app.get("name", ""),
        app.get("description", ""),
        category,
        native_package,
        app.get("flatpak", "") or "",
    ]
    return _normalize_text(" ".join(part for part in parts if part))


# ===============================
# PACKAGE AVAILABILITY / INSTALL STATE
# ===============================

def _run_quiet(cmd: Sequence[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if cmd and cmd[0] in {"apt", "apt-get", "dpkg"}:
        env.setdefault("DEBIAN_FRONTEND", "noninteractive")
    return subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env=env,
    )


@lru_cache(maxsize=2048)
def native_package_available(pkg_name: str, manager: str | None = None) -> bool:
    manager = manager or backend_key()
    if not pkg_name:
        return False

    try:
        if manager == "apt":
            proc = _run_quiet(["apt-cache", "show", pkg_name])
            return proc.returncode == 0 and bool(proc.stdout.strip())

        if manager == "pacman":
            proc = _run_quiet(["pacman", "-Si", "--", pkg_name])
            return proc.returncode == 0

        if manager == "dnf":
            proc = _run_quiet(["dnf", "-q", "info", pkg_name])
            return proc.returncode == 0

        if manager == "zypper":
            proc = _run_quiet(["zypper", "--non-interactive", "info", pkg_name])
            return proc.returncode == 0
    except Exception:
        return False

    return False


@lru_cache(maxsize=2048)
def is_installed(pkg_name: str, manager: str | None = None) -> bool:
    manager = manager or backend_key()
    if not pkg_name:
        return False

    try:
        if manager == "apt":
            proc = _run_quiet(["dpkg", "-s", pkg_name])
            return proc.returncode == 0

        if manager == "pacman":
            proc = _run_quiet(["pacman", "-Q", "--", pkg_name])
            return proc.returncode == 0

        if manager in {"dnf", "zypper"}:
            proc = _run_quiet(["rpm", "-q", pkg_name])
            return proc.returncode == 0
    except Exception:
        return False

    return False


@lru_cache(maxsize=2048)
def is_flatpak_installed(app_id: str) -> bool:
    if not app_id or shutil.which("flatpak") is None:
        return False

    try:
        proc = _run_quiet(["flatpak", "info", app_id])
        return proc.returncode == 0
    except Exception:
        return False



def app_state(app: dict) -> str:
    manager = backend_key()
    native_package = _native_package_for(app, manager)
    flatpak_id = (app.get("flatpak") or "").strip()

    if native_package and is_installed(native_package, manager):
        return "installed-native"
    if flatpak_id and is_flatpak_installed(flatpak_id):
        return "installed-flatpak"
    if native_package and native_package_available(native_package, manager):
        return "available-native"
    if flatpak_id:
        return "available-flatpak"
    return "unavailable"


# ===============================
# UPDATE DETECTION
# ===============================

def _parse_apt_updates(output: str) -> Set[str]:
    updates: Set[str] = set()
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Listing") or "/" not in line:
            continue
        updates.add(line.split("/", 1)[0].strip())
    return updates



def _parse_pacman_updates(output: str) -> Set[str]:
    updates: Set[str] = set()
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        updates.add(line.split()[0])
    return updates



def _parse_dnf_updates(output: str) -> Set[str]:
    updates: Set[str] = set()
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith(("Last metadata expiration", "Obsoleting Packages", "Available Upgrades")):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        name_arch = parts[0]
        if "." in name_arch:
            updates.add(name_arch.rsplit(".", 1)[0])
        else:
            updates.add(name_arch)
    return updates



def _parse_zypper_updates(output: str) -> Set[str]:
    updates: Set[str] = set()
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("Loading", "Reading", "Repository", "S |", "--", "No updates")):
            continue
        if "|" not in raw_line:
            continue

        parts = [part.strip() for part in raw_line.split("|")]
        parts = [part for part in parts if part]
        if len(parts) >= 5 and parts[0].lower() in {"v", "s"}:
            name = parts[2]
        elif len(parts) >= 4:
            name = parts[1]
        else:
            continue

        if name and name.lower() != "name":
            updates.add(name)
    return updates


@lru_cache(maxsize=1)
def _get_native_upgradable_set() -> Set[str]:
    manager = backend_key()

    try:
        if manager == "apt":
            proc = _run_quiet(["apt", "list", "--upgradable"])
            return _parse_apt_updates(proc.stdout)

        if manager == "pacman":
            proc = _run_quiet(["pacman", "-Qu"])
            return _parse_pacman_updates(proc.stdout)

        if manager == "dnf":
            proc = subprocess.run(
                ["dnf", "-q", "check-update"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if proc.returncode not in (0, 100):
                return set()
            return _parse_dnf_updates(proc.stdout)

        if manager == "zypper":
            proc = _run_quiet(["zypper", "--non-interactive", "list-updates"])
            return _parse_zypper_updates(proc.stdout)
    except Exception:
        return set()

    return set()


@lru_cache(maxsize=1)
def _get_flatpak_upgradable_set() -> Set[str]:
    if shutil.which("flatpak") is None:
        return set()

    try:
        proc = _run_quiet(["flatpak", "remote-ls", "--updates", "--app", "--columns=application"])
        if proc.returncode != 0:
            return set()
        return {line.strip() for line in proc.stdout.splitlines() if line.strip() and line.strip() != "application"}
    except Exception:
        return set()


# ===============================
# MAIN DISPLAY LOGIC
# ===============================

def apps_for_display(search: str = "") -> Dict[str, List[dict]]:
    manager = backend_key()
    native_updates = _get_native_upgradable_set()
    flatpak_updates = _get_flatpak_upgradable_set()
    needle = _normalize_text(search)

    result: Dict[str, List[dict]] = {}

    for category, apps in APPS.items():
        visible: List[dict] = []

        for app in apps:
            enriched = deepcopy(app)
            native_package = _native_package_for(app, manager)
            flatpak_id = (app.get("flatpak") or "").strip()
            native_available = native_package_available(native_package, manager)
            flatpak_available = bool(flatpak_id)
            state = app_state(app)

            enriched["native_package"] = native_package
            enriched["native_available"] = native_available
            enriched["flatpak_available"] = flatpak_available
            enriched["state"] = state
            enriched["preferred_source"] = _preferred_source(native_available, flatpak_available)
            enriched["source"] = _requested_source(app, native_available, flatpak_available)
            enriched["search_blob"] = _search_blob(app, category, native_package)

            if state == "installed-native":
                update_available = native_package in native_updates
            elif state == "installed-flatpak":
                update_available = flatpak_id in flatpak_updates
            else:
                update_available = False
            enriched["update_available"] = update_available

            ui = {
                "can_install": False,
                "can_remove": False,
                "can_update": False,
                "color_name": "white",
                "badge": "",
                "status_key": "installer_available",
            }

            if update_available:
                ui.update({
                    "can_update": True,
                    "can_remove": True,
                    "color_name": "purple",
                    "badge": "⬆",
                    "status_key": "installer_update_available",
                })
            elif state in ("installed-native", "installed-flatpak"):
                ui.update({
                    "can_remove": True,
                    "can_update": True,
                    "color_name": "white",
                    "status_key": "installer_installed_native"
                    if state == "installed-native"
                    else "installer_installed_flatpak",
                })
            elif native_available:
                ui.update({
                    "can_install": True,
                    "color_name": "green",
                    "status_key": "installer_available",
                })
            elif flatpak_available:
                ui.update({
                    "can_install": True,
                    "color_name": "orange",
                    "status_key": "installer_available_flatpak",
                })
            else:
                ui.update({
                    "color_name": "red",
                    "status_key": "installer_unavailable",
                })

            enriched["ui"] = ui

            if needle and needle not in enriched["search_blob"]:
                continue

            visible.append(enriched)

        visible.sort(key=_sort_key)

        if visible:
            result[category] = visible

    return result



def _sort_key(app: dict) -> Tuple[int, str]:
    if app.get("update_available"):
        rank = 0
    elif str(app.get("state", "")).startswith("installed"):
        rank = 1
    elif app.get("native_available"):
        rank = 2
    elif app.get("flatpak_available"):
        rank = 3
    else:
        rank = 4

    return (rank, _normalize_text(app.get("name", "")))


# ===============================
# COMMAND EXECUTION
# ===============================

def _with_noninteractive_env(cmd: Sequence[str]) -> List[str]:
    if not cmd:
        return []
    if cmd[0] in {"apt", "apt-get", "dpkg"}:
        return ["env", "DEBIAN_FRONTEND=noninteractive"] + list(cmd)
    return list(cmd)



def _run_command(cmd: Sequence[str], action: str) -> str:
    safe_cmd = _with_noninteractive_env(cmd)

    if helper_available():
        response = send_request({"action": action, "cmd": safe_cmd})
        if response.get("code", 1) != 0:
            raise RuntimeError(response.get("output", "Operation failed."))
        return response.get("output", "").strip()

    elevated = elevated_command(safe_cmd)
    proc = subprocess.run(
        elevated,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if proc.returncode != 0:
        raise RuntimeError(proc.stdout.strip() or "Operation failed.")

    return proc.stdout.strip()



def _native_install_command(packages: Sequence[str]) -> List[str]:
    manager = backend_key()
    packages = [pkg for pkg in packages if pkg]
    if manager == "apt":
        return ["apt", "install", "-y"] + packages
    if manager == "pacman":
        return ["pacman", "-S", "--noconfirm", "--needed"] + packages
    if manager == "dnf":
        return ["dnf", "install", "-y"] + packages
    if manager == "zypper":
        return ["zypper", "--non-interactive", "install"] + packages
    raise RuntimeError(f"Unsupported backend: {manager}")



def _native_remove_command(packages: Sequence[str]) -> List[str]:
    manager = backend_key()
    packages = [pkg for pkg in packages if pkg]
    if manager == "apt":
        return ["apt", "remove", "-y"] + packages
    if manager == "pacman":
        return ["pacman", "-R", "--noconfirm"] + packages
    if manager == "dnf":
        return ["dnf", "remove", "-y"] + packages
    if manager == "zypper":
        return ["zypper", "--non-interactive", "remove"] + packages
    raise RuntimeError(f"Unsupported backend: {manager}")



def _native_update_command(packages: Sequence[str]) -> List[str]:
    manager = backend_key()
    packages = [pkg for pkg in packages if pkg]
    if manager == "apt":
        return ["apt", "install", "-y"] + packages
    if manager == "pacman":
        return ["pacman", "-S", "--noconfirm"] + packages
    if manager == "dnf":
        return ["dnf", "upgrade", "-y"] + packages
    if manager == "zypper":
        return ["zypper", "--non-interactive", "update"] + packages
    raise RuntimeError(f"Unsupported backend: {manager}")



def install_native_packages(packages: List[str]) -> str:
    packages = _deduplicate(packages)
    if not packages:
        return ""
    output = _run_command(_native_install_command(packages), action="install")
    clear_runtime_caches()
    return output



def remove_native_packages(packages: List[str]) -> str:
    packages = _deduplicate(packages)
    if not packages:
        return ""
    output = _run_command(_native_remove_command(packages), action="remove")
    clear_runtime_caches()
    return output



def update_native_packages(packages: List[str]) -> str:
    packages = _deduplicate(packages)
    if not packages:
        return ""
    output = _run_command(_native_update_command(packages), action="update")
    clear_runtime_caches()
    return output



def install_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in _deduplicate(app_ids):
        output_parts.append(_run_command(["flatpak", "install", "-y", "flathub", app_id], action="install"))

    clear_runtime_caches()
    return "\n".join(part for part in output_parts if part)



def remove_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in _deduplicate(app_ids):
        output_parts.append(_run_command(["flatpak", "uninstall", "-y", app_id], action="remove"))

    clear_runtime_caches()
    return "\n".join(part for part in output_parts if part)



def update_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in _deduplicate(app_ids):
        output_parts.append(_run_command(["flatpak", "update", "-y", app_id], action="update"))

    clear_runtime_caches()
    return "\n".join(part for part in output_parts if part)


# ===============================
# COLLECT + HIGH LEVEL ACTIONS
# ===============================

def _collect(selection: List[dict], mode: str) -> Tuple[List[str], List[str], List[str]]:
    manager = backend_key()
    native_packages: List[str] = []
    flatpak_ids: List[str] = []
    errors: List[str] = []

    for app in selection:
        name = app.get("name") or app.get("id") or "Unknown app"
        source = (app.get("source") or "auto").strip().lower()
        if source not in {"native", "flatpak", "auto"}:
            source = "auto"

        native_pkg = (app.get("native_package") or _native_package_for(app, manager)).strip()
        flatpak_id = (app.get("flatpak") or "").strip()
        native_available = native_package_available(native_pkg, manager)
        state = app_state(app)

        if mode == "install":
            if source == "native":
                if native_pkg and native_available:
                    if not is_installed(native_pkg, manager):
                        native_packages.append(native_pkg)
                else:
                    errors.append(f"{name}: native package unavailable on this system.")
                continue

            if source == "flatpak":
                if flatpak_id:
                    if not is_flatpak_installed(flatpak_id):
                        flatpak_ids.append(flatpak_id)
                else:
                    errors.append(f"{name}: Flatpak package unavailable.")
                continue

            if native_pkg and native_available:
                if not is_installed(native_pkg, manager):
                    native_packages.append(native_pkg)
            elif flatpak_id:
                if not is_flatpak_installed(flatpak_id):
                    flatpak_ids.append(flatpak_id)
            else:
                errors.append(f"{name}: no install source available.")
            continue

        if mode == "remove":
            if state == "installed-flatpak" and flatpak_id:
                flatpak_ids.append(flatpak_id)
            elif state == "installed-native" and native_pkg:
                native_packages.append(native_pkg)
            else:
                errors.append(f"{name}: application is not installed.")
            continue

        if mode == "update":
            if state == "installed-flatpak" and flatpak_id:
                flatpak_ids.append(flatpak_id)
            elif state == "installed-native" and native_pkg:
                native_packages.append(native_pkg)
            else:
                errors.append(f"{name}: no installed source available to update.")
            continue

        errors.append(f"{name}: unsupported action '{mode}'.")

    return _deduplicate(native_packages), _deduplicate(flatpak_ids), errors



def _finalize_outputs(outputs: List[str], errors: List[str], empty_message: str) -> str:
    cleaned_outputs = [part.strip() for part in outputs if part and part.strip()]
    if errors:
        cleaned_outputs.append("Skipped:\n- " + "\n- ".join(errors))
    return "\n\n".join(cleaned_outputs).strip() or empty_message



def install_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids, errors = _collect(selection, "install")
    outputs: List[str] = []

    if native_packages:
        outputs.append(install_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(install_flatpak_apps(flatpak_ids))

    return _finalize_outputs(outputs, errors, "Nothing to install.")



def remove_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids, errors = _collect(selection, "remove")
    outputs: List[str] = []

    if native_packages:
        outputs.append(remove_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(remove_flatpak_apps(flatpak_ids))

    return _finalize_outputs(outputs, errors, "Nothing to remove.")



def update_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids, errors = _collect(selection, "update")
    outputs: List[str] = []

    if native_packages:
        outputs.append(update_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(update_flatpak_apps(flatpak_ids))

    return _finalize_outputs(outputs, errors, "Nothing to update.")
