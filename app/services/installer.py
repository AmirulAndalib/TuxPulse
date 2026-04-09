from __future__ import annotations

import os
import shutil
import subprocess
import unicodedata
from copy import deepcopy
from functools import lru_cache
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from core.pkg_backend import PackageBackend
from core.privilege import elevated_command
from services.apps_catalog import APPS

_PACKAGE_BACKEND = PackageBackend()
_SUPPORTED_BACKENDS = ("apt", "pacman", "dnf", "zypper")
_FLATHUB_URL = "https://flathub.org/repo/flathub.flatpakrepo"
_CAPTURE_TIMEOUT = 12
_ACTION_TIMEOUT = 3600


# ===============================
# BACKEND DETECTION
# ===============================

def _normalize_backend_name(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if any(token in raw for token in ("apt", "debian", "ubuntu", "nala")):
        return "apt"
    if any(token in raw for token in ("pacman", "arch", "manjaro", "endeavouros", "cachyos")):
        return "pacman"
    if any(token in raw for token in ("dnf", "fedora", "rhel", "rocky", "alma", "nobara")):
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
        "pm",
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

    if shutil.which("apt") or shutil.which("apt-get"):
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
    _installed_native_set.cache_clear()
    _installed_flatpak_user_set.cache_clear()
    _installed_flatpak_system_set.cache_clear()
    _get_native_upgradable_set.cache_clear()
    _get_flatpak_upgradable_set.cache_clear()
    flatpak_scope_for_app.cache_clear()
    is_installed.cache_clear()
    is_flatpak_installed.cache_clear()



def get_categories() -> Dict[str, List[dict]]:
    return deepcopy(APPS)


def _iter_all_apps() -> Iterable[tuple[str, dict]]:
    for category, apps in APPS.items():
        for app in apps:
            yield category, app


def get_app_definition(app_id: str) -> dict | None:
    app_id = (app_id or '').strip()
    if not app_id:
        return None
    for _category, app in _iter_all_apps():
        if (app.get('id') or '').strip() == app_id:
            return deepcopy(app)
    return None


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
# PROCESS HELPERS
# ===============================

def _run_capture(cmd: Sequence[str], timeout: int = _CAPTURE_TIMEOUT) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if cmd and cmd[0] in {"apt", "apt-get", "dpkg", "apt-cache"}:
        env.setdefault("DEBIAN_FRONTEND", "noninteractive")
    return subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env=env,
        timeout=timeout,
    )



def _run_live(cmd: Sequence[str], *, requires_root: bool = False) -> str:
    final_cmd = list(cmd)
    if requires_root:
        final_cmd = elevated_command(final_cmd)

    proc = subprocess.run(
        final_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=_ACTION_TIMEOUT,
    )
    output = (proc.stdout or "").strip()
    if proc.returncode != 0:
        raise RuntimeError(output or "Operation failed.")
    return output


# ===============================
# FAST LOCAL STATE DETECTION
# ===============================

@lru_cache(maxsize=1)
def _installed_native_set() -> Set[str]:
    manager = backend_key()
    try:
        if manager == "apt":
            proc = _run_capture(["dpkg-query", "-W", "-f=${Package}\n"], timeout=20)
            if proc.returncode != 0:
                return set()
            return {line.strip() for line in (proc.stdout or "").splitlines() if line.strip()}

        if manager == "pacman":
            proc = _run_capture(["pacman", "-Qq"], timeout=20)
            if proc.returncode != 0:
                return set()
            return {line.strip() for line in (proc.stdout or "").splitlines() if line.strip()}

        if manager in {"dnf", "zypper"}:
            proc = _run_capture(["rpm", "-qa", "--qf", "%{NAME}\n"], timeout=30)
            if proc.returncode != 0:
                return set()
            return {line.strip() for line in (proc.stdout or "").splitlines() if line.strip()}
    except Exception:
        return set()

    return set()


@lru_cache(maxsize=1)
def _installed_flatpak_user_set() -> Set[str]:
    if shutil.which("flatpak") is None:
        return set()
    try:
        proc = _run_capture(["flatpak", "list", "--user", "--app", "--columns=application"], timeout=20)
        if proc.returncode != 0:
            return set()
        return {
            line.strip()
            for line in (proc.stdout or "").splitlines()
            if line.strip() and line.strip() != "application"
        }
    except Exception:
        return set()


@lru_cache(maxsize=1)
def _installed_flatpak_system_set() -> Set[str]:
    if shutil.which("flatpak") is None:
        return set()
    try:
        proc = _run_capture(["flatpak", "list", "--system", "--app", "--columns=application"], timeout=20)
        if proc.returncode != 0:
            return set()
        return {
            line.strip()
            for line in (proc.stdout or "").splitlines()
            if line.strip() and line.strip() != "application"
        }
    except Exception:
        return set()


@lru_cache(maxsize=2048)
def flatpak_scope_for_app(app_id: str) -> str | None:
    if not app_id:
        return None
    if app_id in _installed_flatpak_user_set():
        return "user"
    if app_id in _installed_flatpak_system_set():
        return "system"
    return None


@lru_cache(maxsize=2048)
def is_installed(pkg_name: str, manager: str | None = None) -> bool:
    if not pkg_name:
        return False
    return pkg_name in _installed_native_set()


@lru_cache(maxsize=2048)
def is_flatpak_installed(app_id: str) -> bool:
    if not app_id:
        return False
    return flatpak_scope_for_app(app_id) is not None



def app_state(app: dict) -> str:
    manager = backend_key()
    native_package = _native_package_for(app, manager)
    flatpak_id = (app.get("flatpak") or "").strip()

    if native_package and is_installed(native_package, manager):
        return "installed-native"
    if flatpak_id and is_flatpak_installed(flatpak_id):
        return "installed-flatpak"
    if native_package:
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
        updates.add(name_arch.rsplit(".", 1)[0] if "." in name_arch else name_arch)
    return updates



def _parse_zypper_updates(output: str) -> Set[str]:
    updates: Set[str] = set()
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("Loading", "Reading", "Repository", "S |", "--", "No updates")):
            continue
        if "|" not in raw_line:
            continue
        parts = [part.strip() for part in raw_line.split("|") if part.strip()]
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
            proc = _run_capture(["apt", "list", "--upgradable"], timeout=20)
            return _parse_apt_updates(proc.stdout or "") if proc.returncode == 0 else set()

        if manager == "pacman":
            proc = _run_capture(["pacman", "-Qu"], timeout=20)
            return _parse_pacman_updates(proc.stdout or "") if proc.returncode in (0, 1) else set()

        if manager == "dnf":
            proc = subprocess.run(
                ["dnf", "-q", "check-update"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=25,
            )
            return _parse_dnf_updates(proc.stdout or "") if proc.returncode in (0, 100) else set()

        if manager == "zypper":
            proc = _run_capture(["zypper", "--non-interactive", "list-updates"], timeout=25)
            return _parse_zypper_updates(proc.stdout or "") if proc.returncode == 0 else set()
    except Exception:
        return set()

    return set()


@lru_cache(maxsize=1)
def _get_flatpak_upgradable_set() -> Set[str]:
    # Intenționat gol pentru încărcare rapidă și fără apeluri de rețea.
    # Verificarea de updates pentru Flatpak se face la acțiunea de update, nu la afișarea catalogului.
    return set()


# ===============================
# APP ENRICHMENT
# ===============================

def enrich_app_for_display(app: dict, category: str = '') -> dict:
    manager = backend_key()
    native_updates = _get_native_upgradable_set()
    flatpak_updates = _get_flatpak_upgradable_set()

    enriched = deepcopy(app)
    native_package = _native_package_for(app, manager)
    flatpak_id = (app.get('flatpak') or '').strip()
    native_available = bool(native_package)
    flatpak_available = bool(flatpak_id)
    state = app_state(app)

    enriched['native_package'] = native_package
    enriched['native_available'] = native_available
    enriched['flatpak_available'] = flatpak_available
    enriched['state'] = state
    enriched['preferred_source'] = _preferred_source(native_available, flatpak_available)
    enriched['source'] = _requested_source(app, native_available, flatpak_available)
    enriched['search_blob'] = _search_blob(app, category, native_package)

    if state == 'installed-native':
        update_available = native_package in native_updates
    elif state == 'installed-flatpak':
        update_available = flatpak_id in flatpak_updates
    else:
        update_available = False
    enriched['update_available'] = update_available

    ui = {
        'can_install': False,
        'can_remove': False,
        'can_update': False,
        'color_name': 'white',
        'badge': '',
        'status_key': 'installer_available',
    }

    if update_available:
        ui.update({
            'can_update': True,
            'can_remove': True,
            'color_name': 'purple',
            'badge': '⬆',
            'status_key': 'installer_update_available',
        })
    elif state in ('installed-native', 'installed-flatpak'):
        ui.update({
            'can_remove': True,
            'can_update': True,
            'color_name': 'white',
            'status_key': 'installer_installed_native' if state == 'installed-native' else 'installer_installed_flatpak',
        })
    elif native_available:
        ui.update({
            'can_install': True,
            'color_name': 'green',
            'status_key': 'installer_available',
        })
    elif flatpak_available:
        ui.update({
            'can_install': True,
            'color_name': 'orange',
            'status_key': 'installer_available_flatpak',
        })
    else:
        ui.update({
            'color_name': 'red',
            'status_key': 'installer_unavailable',
        })

    enriched['ui'] = ui
    return enriched


def refresh_apps_state(selection: Sequence[dict]) -> Dict[str, dict]:
    refreshed: Dict[str, dict] = {}
    for item in selection:
        app_id = (item.get('id') or '').strip()
        if not app_id:
            continue

        app_def = get_app_definition(app_id) or deepcopy(item)
        source = (item.get('source') or app_def.get('source') or '').strip().lower()
        if source in {'native', 'flatpak'}:
            app_def['source'] = source
        elif 'source' in item:
            app_def['source'] = item.get('source')

        refreshed[app_id] = enrich_app_for_display(app_def)
    return refreshed


# ===============================
# MAIN DISPLAY LOGIC
# ===============================

def apps_for_display(search: str = "") -> Dict[str, List[dict]]:
    needle = _normalize_text(search)

    result: Dict[str, List[dict]] = {}

    for category, apps in APPS.items():
        visible: List[dict] = []

        for app in apps:
            enriched = enrich_app_for_display(app, category)

            if needle and needle not in enriched['search_blob']:
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
# FLATPAK ACTION HELPERS
# ===============================

def _flatpak_available() -> bool:
    return shutil.which("flatpak") is not None



def _flatpak_remote_exists(remote_name: str, scope: str) -> bool:
    if not _flatpak_available():
        return False

    flag = "--user" if scope == "user" else "--system"
    try:
        proc = _run_capture(["flatpak", "remotes", flag, "--columns=name"], timeout=10)
    except Exception:
        return False

    if proc.returncode != 0:
        return False

    remotes = {line.strip() for line in (proc.stdout or "").splitlines() if line.strip()}
    return remote_name in remotes



def _ensure_flathub(scope: str = "user") -> None:
    if not _flatpak_available():
        raise RuntimeError("Flatpak is not installed on this system.")

    if _flatpak_remote_exists("flathub", scope):
        return

    if scope == "user":
        _run_live(["flatpak", "remote-add", "--if-not-exists", "--user", "flathub", _FLATHUB_URL])
    else:
        _run_live(["flatpak", "remote-add", "--if-not-exists", "--system", "flathub", _FLATHUB_URL], requires_root=True)



def _run_flatpak_install_command(app_id: str, scope: str = "user") -> str:
    _ensure_flathub(scope)
    if scope == "user":
        return _run_live(["flatpak", "install", "--user", "-y", "--noninteractive", "flathub", app_id])
    return _run_live(["flatpak", "install", "--system", "-y", "--noninteractive", "flathub", app_id], requires_root=True)



def _run_flatpak_remove_command(app_id: str) -> str:
    scope = flatpak_scope_for_app(app_id) or "user"
    if scope == "user":
        return _run_live(["flatpak", "uninstall", "--user", "-y", "--noninteractive", app_id])
    return _run_live(["flatpak", "uninstall", "--system", "-y", "--noninteractive", app_id], requires_root=True)



def _run_flatpak_update_command(app_id: str) -> str:
    scope = flatpak_scope_for_app(app_id) or "user"
    if scope == "user":
        return _run_live(["flatpak", "update", "--user", "-y", "--noninteractive", app_id])
    return _run_live(["flatpak", "update", "--system", "-y", "--noninteractive", app_id], requires_root=True)


# ===============================
# NATIVE ACTION HELPERS
# ===============================

def _native_install_command(packages: Sequence[str]) -> List[str]:
    manager = backend_key()
    packages = [pkg for pkg in packages if pkg]
    if manager == "apt":
        return ["env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y"] + packages
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
        return ["env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "remove", "-y"] + packages
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
        return ["env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "--only-upgrade", "-y"] + packages
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
    output = _run_live(_native_install_command(packages), requires_root=True)
    clear_runtime_caches()
    return output



def remove_native_packages(packages: List[str]) -> str:
    packages = _deduplicate(packages)
    if not packages:
        return ""
    output = _run_live(_native_remove_command(packages), requires_root=True)
    clear_runtime_caches()
    return output



def update_native_packages(packages: List[str]) -> str:
    packages = _deduplicate(packages)
    if not packages:
        return ""
    output = _run_live(_native_update_command(packages), requires_root=True)
    clear_runtime_caches()
    return output



def install_flatpak_apps(app_ids: List[str]) -> str:
    if not _flatpak_available():
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in _deduplicate(app_ids):
        output_parts.append(_run_flatpak_install_command(app_id, scope="user"))

    clear_runtime_caches()
    return "\n".join(part for part in output_parts if part)



def remove_flatpak_apps(app_ids: List[str]) -> str:
    if not _flatpak_available():
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in _deduplicate(app_ids):
        output_parts.append(_run_flatpak_remove_command(app_id))

    clear_runtime_caches()
    return "\n".join(part for part in output_parts if part)



def update_flatpak_apps(app_ids: List[str]) -> str:
    if not _flatpak_available():
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in _deduplicate(app_ids):
        output_parts.append(_run_flatpak_update_command(app_id))

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
        native_available = bool(native_pkg)
        state = app_state(app)

        if mode == "install":
            if source == "native":
                if native_available:
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

            if native_available:
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
                errors.append(f"{name}: application is not installed.")
            continue

    return _deduplicate(native_packages), _deduplicate(flatpak_ids), errors



def _join_outputs(parts: Iterable[str]) -> str:
    return "\n\n".join(part.strip() for part in parts if part and part.strip())



def install_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids, errors = _collect(selection, "install")
    outputs: List[str] = []

    if native_packages:
        outputs.append(install_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(install_flatpak_apps(flatpak_ids))
    if errors:
        outputs.append("\n".join(errors))
    if not native_packages and not flatpak_ids and not errors:
        outputs.append("No selected applications required installation.")

    return _join_outputs(outputs)



def remove_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids, errors = _collect(selection, "remove")
    outputs: List[str] = []

    if native_packages:
        outputs.append(remove_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(remove_flatpak_apps(flatpak_ids))
    if errors:
        outputs.append("\n".join(errors))
    if not native_packages and not flatpak_ids and not errors:
        outputs.append("No selected applications required removal.")

    return _join_outputs(outputs)



def update_apps(selection: List[dict]) -> str:
    native_packages, flatpak_ids, errors = _collect(selection, "update")
    outputs: List[str] = []

    if native_packages:
        outputs.append(update_native_packages(native_packages))
    if flatpak_ids:
        outputs.append(update_flatpak_apps(flatpak_ids))
    if errors:
        outputs.append("\n".join(errors))
    if not native_packages and not flatpak_ids and not errors:
        outputs.append("No selected applications required update.")

    return _join_outputs(outputs)



def install_one_app(app: dict) -> str:
    return install_apps([app])



def remove_one_app(app: dict) -> str:
    return remove_apps([app])



def update_one_app(app: dict) -> str:
    return update_apps([app])



def helper_available(timeout: float = 2.0) -> bool:
    return False
