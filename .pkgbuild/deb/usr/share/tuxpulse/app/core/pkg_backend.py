import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from core.platform import detect_platform


class PackageBackend:
    def __init__(self) -> None:
        self.platform = detect_platform()
        self.pm = self.platform.package_manager

    def maintenance_steps(self) -> List[Tuple[str, str]]:
        """Returnează pașii de mentenanță completă cu comenzi stabile (fără warning-uri apt)."""
        if self.pm != "apt":
            return []

        return [
            ("Update package lists", "apt-get update"),
            ("Upgrade system packages", "apt-get upgrade -y"),
            ("Remove old packages and configs", "apt-get autopurge -y"),
            ("Remove unused packages", "apt-get autoremove -y"),
            ("Clean package cache", "apt-get autoclean"),
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
                ["apt-get", "upgrade", "--dry-run", "--quiet"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            # Alternativă mai stabilă decât "apt list --upgradable"
            items: List[Dict[str, str]] = []
            for line in output.splitlines():
                line = line.strip()
                if not line or "=>" not in line:
                    continue

                # Extragem numele pachetului
                parts = line.split()
                if not parts:
                    continue
                name = parts[0].split("/")[0] if "/" in parts[0] else parts[0]

                items.append(
                    {
                        "name": name,
                        "version": "upgradable",
                        "status": "upgradable",
                    }
                )
                if limit is not None and len(items) >= limit:
                    break
            return items
        except Exception:
            # Fallback la varianta veche dacă e necesar
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
                    name = line.split("/", 1)[0]
                    items.append({"name": name, "version": "upgradable", "status": "upgradable"})
                    if limit is not None and len(items) >= limit:
                        break
                return items
            except Exception:
                return []

    def remove_cmd(self, name: str) -> List[str]:
        if self.pm != "apt":
            raise RuntimeError("No supported package manager found.")
        return ["apt-get", "remove", "-y", name]

    def purge_cmd(self, name: str) -> List[str]:
        if self.pm != "apt":
            raise RuntimeError("No supported package manager found.")
        return ["apt-get", "purge", "-y", name]

    def has_flatpak(self) -> bool:
        return shutil.which("flatpak") is not None