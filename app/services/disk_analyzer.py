import heapq
import os
import shutil
from pathlib import Path
from typing import Callable


ProgressCallback = Callable[[str], None]


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


def _emit_progress(progress_cb: ProgressCallback | None, message: str):
    if callable(progress_cb):
        progress_cb(message)


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


def get_home_top_directories(limit=8, progress_cb: ProgressCallback | None = None):
    home = Path.home()
    items = []
    try:
        directories = [entry for entry in home.iterdir() if entry.is_dir()]
    except OSError:
        return []

    total_dirs = max(1, len(directories))
    for index, entry in enumerate(directories, start=1):
        _emit_progress(progress_cb, f"Scanning folders {index}/{total_dirs}: {entry.name}")
        size_mb = _dir_size_mb(entry)
        items.append({'name': entry.name, 'size_mb': round(size_mb, 1)})

    items.sort(key=lambda x: x['size_mb'], reverse=True)
    return items[:limit]


def get_home_largest_files(limit=20, progress_cb: ProgressCallback | None = None):
    home = Path.home()
    heap: list[tuple[int, str]] = []
    visited_dirs = 0

    for root, _, filenames in os.walk(home, onerror=lambda _e: None):
        visited_dirs += 1
        if visited_dirs % 40 == 0:
            _emit_progress(progress_cb, f"Scanning files in: {root}")

        for name in filenames:
            path = Path(root) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue

            item = (size, str(path))
            if len(heap) < limit:
                heapq.heappush(heap, item)
            elif size > heap[0][0]:
                heapq.heapreplace(heap, item)

    largest = [
        {'path': path, 'size_mb': round(size / (1024 ** 2), 2)}
        for size, path in sorted(heap, key=lambda entry: entry[0], reverse=True)
    ]
    return largest


def build_disk_analysis(limit_dirs=8, limit_files=20, progress_cb: ProgressCallback | None = None):
    _emit_progress(progress_cb, 'Reading disk usage...')
    usage = get_root_usage()

    _emit_progress(progress_cb, 'Collecting largest directories...')
    directories = get_home_top_directories(limit=limit_dirs, progress_cb=progress_cb)

    _emit_progress(progress_cb, 'Collecting largest files...')
    files = get_home_largest_files(limit=limit_files, progress_cb=progress_cb)

    _emit_progress(progress_cb, 'Preparing results...')
    return {
        'usage': usage,
        'directories': directories,
        'files': files,
    }
