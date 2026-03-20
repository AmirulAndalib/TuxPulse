import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from core.platform import detect_platform


class PackageBackend:
    def __init__(self) -> None:
        self.platform = detect_platform()
        self.pm = self.platform.package_manager

    def maintenance_steps(self) -> List[Tuple[str, str]]:
        if self.pm == "apt":
            return [
                ("Update package lists", "apt update"),
                ("Upgrade system packages", "apt full-upgrade -y"),
                ("Remove unused packages", "apt autoremove -y"),
                ("Clean package cache", "apt autoclean"),
            ]

        if self.pm == "pacman":
            return [
                ("Synchronize package databases", "pacman -Sy"),
                ("Upgrade system packages", "pacman -Syu --noconfirm"),
                (
                    "Remove orphan packages",
                    "orphans=$(pacman -Qtdq 2>/dev/null || true); "
                    '[ -n "$orphans" ] && pacman -Rns --noconfirm $orphans || true',
                ),
                ("Clean package cache", "pacman -Sc --noconfirm"),
            ]

        if self.pm == "dnf":
            return [
                ("Upgrade system packages", "dnf upgrade -y"),
                ("Remove unused packages", "dnf autoremove -y"),
                ("Clean package cache", "dnf clean all"),
            ]

        if self.pm == "zypper":
            return [
                ("Refresh repositories", "zypper --non-interactive refresh"),
                ("Upgrade system packages", "zypper --non-interactive update"),
                ("Clean package cache", "zypper clean --all"),
            ]

        return []

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
        try:
            if self.pm == "apt":
                output = subprocess.check_output(
                    ["dpkg-query", "-W", "-f=${Package}\t${Version}\n"],
                    text=True,
                )
                return self._parse_name_version_lines(output, search=search, limit=limit)

            if self.pm == "pacman":
                output = subprocess.check_output(["pacman", "-Q"], text=True)
                return self._parse_name_version_lines(output, search=search, limit=limit)

            if self.pm in {"dnf", "zypper"}:
                output = subprocess.check_output(
                    ["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}-%{RELEASE}\n"],
                    text=True,
                )
                return self._parse_name_version_lines(output, search=search, limit=limit)

        except Exception:
            return []

        return []

    def count_installed(self) -> int:
        items = self.list_installed(limit=None)
        return len(items)

    def list_upgradable(self, limit: Optional[int] = 300) -> List[Dict[str, str]]:
        if self.pm == "apt":
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
                    items.append({"name": name, "version": version, "status": "upgradable"})
                    if limit is not None and len(items) >= limit:
                        break
                return items
            except Exception:
                return []

        if self.pm == "pacman":
            try:
                output = subprocess.check_output(
                    ["pacman", "-Qu"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                items: List[Dict[str, str]] = []
                for line in output.splitlines():
                    parts = line.split()
                    if len(parts) >= 2:
                        items.append(
                            {
                                "name": parts[0],
                                "version": parts[1],
                                "status": "upgradable",
                            }
                        )
                    if limit is not None and len(items) >= limit:
                        break
                return items
            except subprocess.CalledProcessError as exc:
                # pacman -Qu poate returna nenul când nu sunt actualizări
                if exc.returncode != 0 and not exc.output:
                    return []
                return []
            except Exception:
                return []

        if self.pm == "dnf":
            try:
                output = subprocess.check_output(
                    ["dnf", "check-update", "--quiet"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                return self._parse_dnf_updates(output, limit=limit)
            except subprocess.CalledProcessError as exc:
                # dnf check-update:
                # 0 = nu sunt update-uri
                # 100 = sunt update-uri disponibile
                if exc.returncode == 100:
                    return self._parse_dnf_updates(exc.output or "", limit=limit)
                return []
            except Exception:
                return []

        if self.pm == "zypper":
            try:
                output = subprocess.check_output(
                    ["zypper", "--non-interactive", "list-updates"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                items: List[Dict[str, str]] = []
                for line in output.splitlines():
                    line = line.strip()
                    if "|" not in line:
                        continue
                    cols = [col.strip() for col in line.split("|")]
                    if len(cols) >= 5 and cols[0].isdigit():
                        items.append(
                            {
                                "name": cols[2],
                                "version": cols[4],
                                "status": "upgradable",
                            }
                        )
                    if limit is not None and len(items) >= limit:
                        break
                return items
            except Exception:
                return []

        return []

    def _parse_dnf_updates(self, output: str, limit: Optional[int] = 300) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith(("Last metadata expiration check:", "Obsoleting Packages", "Security:")):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            name_arch = parts[0]
            version = parts[1]

            # Ex: python3.x86_64
            name = name_arch.rsplit(".", 1)[0] if "." in name_arch else name_arch

            items.append({"name": name, "version": version, "status": "upgradable"})
            if limit is not None and len(items) >= limit:
                break

        return items

    def remove_cmd(self, name: str) -> List[str]:
        if self.pm == "apt":
            return ["apt", "remove", "-y", name]
        if self.pm == "pacman":
            return ["pacman", "-R", "--noconfirm", name]
        if self.pm == "dnf":
            return ["dnf", "remove", "-y", name]
        if self.pm == "zypper":
            return ["zypper", "--non-interactive", "remove", name]
        raise RuntimeError("No supported package manager found.")

    def purge_cmd(self, name: str) -> List[str]:
        if self.pm == "apt":
            return ["apt", "purge", "-y", name]
        return self.remove_cmd(name)

    def has_flatpak(self) -> bool:
        return shutil.which("flatpak") is not None