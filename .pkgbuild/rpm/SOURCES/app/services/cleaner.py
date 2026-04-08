from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from core.privilege import elevated_command


def get_cleaner_targets():
    return [
        {
            "name": "Thumbnail cache",
            "path": str(Path.home() / ".cache" / "thumbnails"),
            "requires_root": False,
        },
        {
            "name": "User cache",
            "path": str(Path.home() / ".cache"),
            "requires_root": False,
        },
        {
            "name": "Trash",
            "path": str(Path.home() / ".local/share/Trash"),
            "requires_root": False,
        },
        {
            "name": "Temporary files",
            "path": "/tmp",
            "requires_root": True,
        },
        {
            "name": "Vacuum journal (7 days)",
            "path": "journalctl --vacuum-time=7d",
            "requires_root": True,
        },
        {
            "name": "Remove orphan packages",
            "path": "package-orphans",
            "requires_root": True,
        },
    ]


def _clear_directory(path: Path):
    if not path.exists() or not path.is_dir():
        return

    for item in path.iterdir():
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            try:
                item.unlink()
            except OSError:
                pass


def empty_trash():
    trash_root = Path.home() / ".local/share/Trash"
    _clear_directory(trash_root / "files")
    _clear_directory(trash_root / "info")


def clean_target(target_name):
    if target_name == "Trash":
        return {"kind": "python", "name": target_name}
    if target_name == "Vacuum journal (7 days)":
        return vacuum_journal(days=7)
    if target_name == "Remove orphan packages":
        return cleanup_orphan_packages()

    for target in get_cleaner_targets():
        if target["name"] != target_name:
            continue

        path = Path(target["path"])

        if target["requires_root"]:
            return {
                "kind": "command",
                "command": [
                    "sh",
                    "-c",
                    f'find "{path}" -mindepth 1 -maxdepth 1 -exec rm -rf {{}} +',
                ],
                "requires_root": True,
            }

        if path.name == "cache" and str(path) == str(Path.home() / ".cache"):
            if path.exists() and path.is_dir():
                for item in path.iterdir():
                    if item.name == "Trash":
                        continue
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        try:
                            item.unlink()
                        except OSError:
                            pass
            return None

        _clear_directory(path)
        return None

    return None


def vacuum_journal(days=7):
    return {
        "kind": "command",
        "command": ["journalctl", f"--vacuum-time={days}d"],
        "requires_root": True,
    }


def run_clean_command(command, output_callback=None):
    if isinstance(command, dict) and command.get("kind") == "python":
        if output_callback:
            output_callback(f">>> {command.get('name', 'task')}")
        if command.get("name") == "Trash":
            empty_trash()
        return 0

    if command is None:
        return 0

    requires_root = False
    actual_command = command

    if isinstance(command, dict) and command.get("kind") == "command":
        actual_command = list(command.get("command", []))
        requires_root = bool(command.get("requires_root"))
    elif isinstance(command, (list, tuple)):
        actual_command = list(command)

    try:
        if requires_root:
            actual_command = elevated_command(actual_command)
    except RuntimeError as exc:
        if output_callback:
            output_callback(str(exc))
        raise

    process = subprocess.Popen(
        actual_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if process.stdout is not None:
        for line in process.stdout:
            if output_callback:
                output_callback(line.rstrip("\n"))

    process.wait()
    return process.returncode


def cleanup_orphan_packages():
    from core.pkg_backend import PackageBackend

    pm = PackageBackend().pm

    if pm == "apt":
        return {
            "kind": "command",
            "command": ["apt", "autoremove", "-y"],
            "requires_root": True,
        }

    if pm == "pacman":
        return {
            "kind": "command",
            "command": [
                "bash",
                "-lc",
                'orphans=$(pacman -Qtdq 2>/dev/null || true); [ -n "$orphans" ] && pacman -Rns --noconfirm $orphans || true',
            ],
            "requires_root": True,
        }

    if pm == "dnf":
        return {
            "kind": "command",
            "command": ["dnf", "autoremove", "-y"],
            "requires_root": True,
        }

    if pm == "zypper":
        return {
            "kind": "command",
            "command": [
                "bash",
                "-lc",
                "pkgs=$(zypper packages --unneeded 2>/dev/null | awk -F'|' '/^i/ {print $3}' | xargs); [ -n \"$pkgs\" ] && zypper --non-interactive remove --clean-deps $pkgs || true",
            ],
            "requires_root": True,
        }

    raise RuntimeError("Unsupported distribution.")
