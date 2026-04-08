from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class PlatformInfo:
    family: str          # debian / fedora / opensuse / arch / unknown
    package_manager: str # apt / dnf / zypper / pacman / unknown
    python_cmd: str      # python3
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
    distro_id_like = f"{distro_id} {distro_like}".strip()

    # Debian family
    if distro_id in {"ubuntu", "debian", "linuxmint", "pop", "elementary"} or "debian" in distro_id_like:
        return PlatformInfo("debian", "apt", "python3", "pkexec")

    # Fedora family
    if distro_id in {"fedora", "rhel", "centos", "rocky", "alma", "nobara"} or "fedora" in distro_id_like:
        return PlatformInfo("fedora", "dnf", "python3", "pkexec")

    # openSUSE
    if distro_id in {"opensuse", "opensuse-leap", "opensuse-tumbleweed"} or "suse" in distro_id_like:
        return PlatformInfo("opensuse", "zypper", "python3", "pkexec")

    # Arch / Manjaro / EndeavourOS etc.
    if distro_id in {"arch", "manjaro", "endeavouros"} or "arch" in distro_id_like:
        return PlatformInfo("arch", "pacman", "python3", "pkexec")

    return PlatformInfo("unknown", "unknown", "python3", "pkexec")