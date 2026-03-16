import shutil
import subprocess
from pathlib import Path


def get_cleaner_targets():
    return [
        {"name": "Thumbnail cache", "path": str(Path.home() / ".cache" / "thumbnails"), "requires_root": False},
        {"name": "User cache", "path": str(Path.home() / ".cache"), "requires_root": False},
        {"name": "Trash", "path": str(Path.home() / ".local/share/Trash"), "requires_root": False},
        {"name": "Temporary files", "path": "/tmp", "requires_root": True},
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

    for target in get_cleaner_targets():
        if target["name"] == target_name:
            path = Path(target["path"])
            if target["requires_root"]:
                return ["pkexec", "sh", "-c", f'rm -rf "{path}"/*']

            if path.name == "cache" and str(path) == str(Path.home() / ".cache"):
                # keep application runtime files safer by not deleting nested Trash here
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
    return ["pkexec", "journalctl", f"--vacuum-time={days}d"]


def run_clean_command(command, output_callback=None):
    if isinstance(command, dict) and command.get("kind") == "python":
        if output_callback:
            output_callback(f">>> {command.get('name', 'task')}")
        if command.get("name") == "Trash":
            empty_trash()
        return 0

    if command is None:
        return 0

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if process.stdout is not None:
        for line in process.stdout:
            if output_callback:
                output_callback(line)
    process.wait()
    return process.returncode
