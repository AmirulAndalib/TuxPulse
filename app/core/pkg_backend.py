import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from core.platform import detect_platform


class PackageBackend:
    def __init__(self) -> None:
        self.platform = detect_platform()
        self.pm = self.platform.package_manager

    def maintenance_steps(self) -> List[Tuple[str, str]]:
        if self.pm != "apt":
            return []
        return [
            ("Update package lists", "apt update"),
            ("Upgrade system packages", "apt upgrade -y"),
            ("Remove old packages and configs", "apt autopurge -y || true"),
            ("Remove unused packages", "apt autoremove -y || true"),
            ("Clean package cache", "apt autoclean || true"),
        ]

    def _parse_name_version_lines(
        self,
        output: str,
        search: str = "",
        limit: Optional[int] = 300,
    ) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        needle = search.lower().strip()

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            if "\t" in line:
                name, version = line.split("\t", 1)
            else:
                parts = line.split(maxsplit=1)
                name = parts[0]
                version = parts[1] if len(parts) > 1 else ""

            if needle and needle not in name.lower():
                continue

            items.append(
                {
                    "name": name,
                    "version": version,
                    "status": "installed",
                }
            )

            if limit is not None and len(items) >= limit:
                break

        return items

    def list_installed(self, search: str = "", limit: Optional[int] = 300) -> List[Dict[str, str]]:
        if self.pm != "apt":
            return []

        try:
            output = subprocess.check_output(
                ["dpkg-query", "-W", "-f=${Package}\t${Version}\n"],
                text=True,
            )
            return self._parse_name_version_lines(output, search=search, limit=limit)
        except Exception:
            return []

    def count_installed(self) -> int:
        if self.pm != "apt":
            return 0

        try:
            output = subprocess.check_output(
                ["dpkg-query", "-W", "-f=${Package}\n"],
                text=True,
            )
            return sum(1 for line in output.splitlines() if line.strip())
        except Exception:
            return 0

    def list_upgradable(self, limit: Optional[int] = 300) -> List[Dict[str, str]]:
        if self.pm != "apt":
            return []

        try:
            output = subprocess.check_output(
                ["apt", "list", "--upgradable"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            items: List[Dict[str, str]] = []
            for line in output.splitlines():
                line = line.strip()
                if not line or "/" not in line or line.startswith("Listing..."):
                    continue

                parts = line.split()
                name = line.split("/", 1)[0]
                version = parts[1] if len(parts) > 1 else "upgradable"
                items.append(
                    {
                        "name": name,
                        "version": version,
                        "status": "upgradable",
                    }
                )
                if limit is not None and len(items) >= limit:
                    break
            return items
        except Exception:
            return []

    def remove_cmd(self, name: str) -> List[str]:
        if self.pm != "apt":
            raise RuntimeError("No supported package manager found.")
        return ["apt", "remove", "-y", name]

    def purge_cmd(self, name: str) -> List[str]:
        if self.pm != "apt":
            raise RuntimeError("No supported package manager found.")
        return ["apt", "purge", "-y", name]

    def has_flatpak(self) -> bool:
        return shutil.which("flatpak") is not None
