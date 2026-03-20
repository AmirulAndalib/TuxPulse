from dataclasses import dataclass
from typing import Dict
import shutil


@dataclass(frozen=True)
class PlatformInfo:
    family: str          # debian, arch, fedora, opensuse, unknown
    package_manager: str # apt, pacman, dnf, zypper, unknown
    python_cmd: str      # python3 / python
    pkexec_cmd: str      # pkexec


def _read_os_release() -> Dict[str, str]:
    data: Dict[str, str] = {}
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                data[key] = value.strip().strip('"')
    except OSError:
        pass
    return data


def detect_platform() -> PlatformInfo:
    osr = _read_os_release()
    distro_id = osr.get("ID", "").lower()
    distro_like = osr.get("ID_LIKE", "").lower()

    if distro_id in {"ubuntu", "debian", "linuxmint", "pop"} or "debian" in distro_like:
        return PlatformInfo("debian", "apt", "python3", "pkexec")

    if distro_id in {"arch", "endeavouros", "manjaro"} or "arch" in distro_like:
        return PlatformInfo("arch", "pacman", "python", "pkexec")

    if distro_id in {"fedora"} or "fedora" in distro_like or "rhel" in distro_like:
        return PlatformInfo("fedora", "dnf", "python3", "pkexec")

    if (
        distro_id in {"opensuse-tumbleweed", "opensuse-leap", "opensuse", "opensuse-slowroll", "sles"}
        or "suse" in distro_like
    ):
        return PlatformInfo("opensuse", "zypper", "python3", "pkexec")

    if shutil.which("apt"):
        return PlatformInfo("debian", "apt", "python3", "pkexec")
    if shutil.which("pacman"):
        return PlatformInfo("arch", "pacman", "python", "pkexec")
    if shutil.which("dnf"):
        return PlatformInfo("fedora", "dnf", "python3", "pkexec")
    if shutil.which("zypper"):
        return PlatformInfo("opensuse", "zypper", "python3", "pkexec")

    return PlatformInfo("unknown", "unknown", "python3", "pkexec")