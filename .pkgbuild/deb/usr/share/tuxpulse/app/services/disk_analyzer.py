import os
import shutil
from pathlib import Path


def get_root_usage():
    usage = shutil.disk_usage('/')
    used_gb = usage.used / (1024 ** 3)
    free_gb = usage.free / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    return {
        'used_gb': used_gb,
        'free_gb': free_gb,
        'total_gb': total_gb,
    }


def _dir_size_mb(path: Path) -> float:
    total = 0
    try:
        for root, _, files in os.walk(path, onerror=lambda _e: None):
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    continue
    except OSError:
        return 0.0
    return total / (1024 ** 2)


def get_home_top_directories(limit=8):
    home = Path.home()
    items = []
    for entry in home.iterdir():
        if not entry.is_dir():
            continue
        size_mb = _dir_size_mb(entry)
        items.append({'name': entry.name, 'size_mb': round(size_mb, 1)})
    items.sort(key=lambda x: x['size_mb'], reverse=True)
    return items[:limit]


def get_home_largest_files(limit=20):
    home = Path.home()
    files = []
    for root, _, filenames in os.walk(home, onerror=lambda _e: None):
        for name in filenames:
            path = Path(root) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            files.append({'path': str(path), 'size_mb': round(size / (1024 ** 2), 2)})
    files.sort(key=lambda x: x['size_mb'], reverse=True)
    return files[:limit]
