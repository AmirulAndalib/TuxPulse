from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class PlatformInfo:
    family: str          # debian / unknown
    package_manager: str # apt / unknown
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

    if distro_id in {"ubuntu", "debian", "linuxmint", "pop"} or "debian" in distro_like:
        return PlatformInfo("debian", "apt", "python3", "pkexec")

    return PlatformInfo("unknown", "unknown", "python3", "pkexec")