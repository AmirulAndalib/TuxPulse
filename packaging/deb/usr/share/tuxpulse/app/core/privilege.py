import os
import shutil
import stat
from typing import List, Sequence


def _which(name: str) -> str:
    return shutil.which(name) or ""


def is_root() -> bool:
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def pkexec_is_usable() -> bool:
    path = _which("pkexec")
    if not path:
        return False
    try:
        st = os.stat(path)
    except OSError:
        return False
    return bool(st.st_mode & stat.S_ISUID)


def sudo_is_available() -> bool:
    return bool(_which("sudo"))


def elevation_error_message(non_interactive: bool = False) -> str:
    path = _which("pkexec")
    if path and not pkexec_is_usable():
        msg = (
            "Administrative actions are unavailable because pkexec is installed "
            "without the setuid root bit. Fix it with: sudo chown root:root "
            f"{path} && sudo chmod 4755 {path}"
        )
        if non_interactive:
            msg += " For scheduled tasks, configure sudo NOPASSWD instead of pkexec."
        return msg
    if non_interactive:
        return (
            "Administrative scheduled tasks require sudo with NOPASSWD enabled for the current user. "
            "pkexec cannot be used from cron."
        )
    if not path and not sudo_is_available():
        return "Neither pkexec nor sudo is available for administrative actions."
    return "Unable to elevate privileges for the requested administrative action."


def elevation_prefix(non_interactive: bool = False) -> List[str]:
    if is_root():
        return []
    if non_interactive:
        if sudo_is_available():
            return ["sudo", "-n"]
        raise RuntimeError(elevation_error_message(non_interactive=True))
    if pkexec_is_usable():
        return ["pkexec"]
    if sudo_is_available():
        return ["sudo"]
    raise RuntimeError(elevation_error_message(non_interactive=False))


def elevated_command(command: Sequence[str], non_interactive: bool = False) -> List[str]:
    return elevation_prefix(non_interactive=non_interactive) + list(command)
