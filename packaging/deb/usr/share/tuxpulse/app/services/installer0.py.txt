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


# ===============================
# HELPERS
# ===============================

def get_categories() -> Dict[str, List[dict]]:
    return deepcopy(APPS)


def _native_package_for(app: dict) -> str:
    return app.get("packages", {}).get("apt", "")


@lru_cache(maxsize=512)
def native_package_available(pkg_name: str) -> bool:
    if not pkg_name:
        return False
    try:
        proc = subprocess.run(
            ["apt-cache", "show", pkg_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return proc.returncode == 0 and bool(proc.stdout.strip())
    except Exception:
        return False


def is_installed(pkg_name: str) -> bool:
    if not pkg_name:
        return False
    try:
        subprocess.check_output(["dpkg", "-s", pkg_name], stderr=subprocess.DEVNULL)
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


# ===============================
# UPDATE DETECTION
# ===============================

def _get_upgradable_set():
    try:
        output = subprocess.check_output(
            ["apt", "list", "--upgradable"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        result = set()
        for line in output.splitlines():
            if "/" in line and not line.startswith("Listing"):
                result.add(line.split("/", 1)[0])
        return result
    except Exception:
        return set()


# ===============================
# MAIN DISPLAY LOGIC
# ===============================

def apps_for_display(search: str = "") -> Dict[str, List[dict]]:
    upgradable = _get_upgradable_set()
    needle = (search or "").strip().lower()

    result: Dict[str, List[dict]] = {}

    for category, apps in APPS.items():
        visible = []

        for app in apps:
            enriched = deepcopy(app)

            # --- base ---
            enriched["native_package"] = _native_package_for(app)
            enriched["native_available"] = native_package_available(enriched["native_package"])
            enriched["flatpak_available"] = bool(app.get("flatpak"))
            enriched["state"] = app_state(app)

            # --- source ---
            if not enriched["native_available"] and enriched["flatpak_available"]:
                enriched["source"] = "flatpak"
            else:
                enriched["source"] = "native"

            # --- update ---
            pkg = enriched["native_package"]
            enriched["update_available"] = pkg in upgradable

            state = enriched["state"]
            native_available = enriched["native_available"]
            flatpak_available = enriched["flatpak_available"]

            # ===============================
            # UI LOGIC (UX FINAL)
            # ===============================
            ui = {
                "can_install": False,
                "can_remove": False,
                "can_update": False,
                "color_name": "white",
                "badge": "",
                "status_key": "installer_available",
            }

            # 🔼 UPDATE (PRIORITY)
            if enriched["update_available"]:
                ui.update({
                    "can_update": True,
                    "color_name": "purple",
                    "badge": "⬆",
                    "status_key": "installer_update_available",
                })

            # ✔ INSTALLED (NO COLOR)
            elif state in ("installed-native", "installed-flatpak"):
                ui.update({
                    "can_remove": True,
                    "can_update": True,
                    "color_name": "white",
                    "status_key": "installer_installed_native"
                        if state == "installed-native"
                        else "installer_installed_flatpak",
                })

            # 🟢 AVAILABLE NATIVE
            elif native_available:
                ui.update({
                    "can_install": True,
                    "color_name": "green",
                    "status_key": "installer_available",
                })

            # 🟠 AVAILABLE FLATPAK
            elif flatpak_available:
                ui.update({
                    "can_install": True,
                    "color_name": "orange",
                    "status_key": "installer_available_flatpak",
                })

            # 🔴 UNAVAILABLE
            else:
                ui.update({
                    "color_name": "red",
                    "status_key": "installer_unavailable",
                })

            enriched["ui"] = ui

            # --- search ---
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

        # ===============================
        # SORT UX
        # ===============================
        def sort_key(app):
            if app.get("update_available"):
                return (0,)
            if app["state"].startswith("installed"):
                return (1,)
            if app.get("native_available"):
                return (2,)
            if app.get("flatpak_available"):
                return (3,)
            return (4,)

        visible.sort(key=sort_key)

        if visible:
            result[category] = visible

    return result


# ===============================
# COMMAND EXECUTION
# ===============================

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
    return _run_command(["apt", "install", "-y"] + packages, action="install")


def remove_native_packages(packages: List[str]) -> str:
    packages = [p for p in packages if p]
    if not packages:
        return ""
    return _run_command(["apt", "remove", "-y"] + packages, action="remove")


def update_native_packages(packages: List[str]) -> str:
    packages = [p for p in packages if p]
    if not packages:
        return ""
    return _run_command(["apt", "install", "-y"] + packages, action="update")


def install_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in [a for a in app_ids if a]:
        output_parts.append(_run_command(["flatpak", "install", "-y", "flathub", app_id]))

    return "\n".join(output_parts)


def remove_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in [a for a in app_ids if a]:
        output_parts.append(_run_command(["flatpak", "uninstall", "-y", app_id]))

    return "\n".join(output_parts)


def update_flatpak_apps(app_ids: List[str]) -> str:
    if shutil.which("flatpak") is None:
        raise RuntimeError("Flatpak is not installed on this system.")

    output_parts = []
    for app_id in [a for a in app_ids if a]:
        output_parts.append(_run_command(["flatpak", "update", "-y", app_id]))

    return "\n".join(output_parts)

# ===============================
# COLLECT + HIGH LEVEL ACTIONS
# ===============================

def _collect(selection: List[dict], mode: str):
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