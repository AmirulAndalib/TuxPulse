import os
import platform
import shutil
import socket
import time
from datetime import datetime

import psutil


def build_system_summary():
    uname = platform.uname()
    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
    total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    disk = psutil.disk_usage('/')
    hostname = socket.gethostname()
    lines = [
        f'Hostname: {hostname}',
        f'System: {uname.system} {uname.release}',
        f'Node: {uname.node}',
        f'Machine: {uname.machine}',
        f'Processor: {uname.processor or "Unknown"}',
        f'Boot time: {boot_time}',
        f'CPU cores (logical): {psutil.cpu_count(logical=True)}',
        f'RAM total: {total_ram_gb:.2f} GiB',
        f'RAM used: {psutil.virtual_memory().percent:.1f}%',
        f'Root usage: {disk.percent:.1f}% ({disk.used / (1024 ** 3):.2f} / {disk.total / (1024 ** 3):.2f} GiB)',
        f'Python: {platform.python_version()}',
        f'Home free space: {shutil.disk_usage(os.path.expanduser("~")).free / (1024 ** 3):.2f} GiB',
    ]
    return '\n'.join(lines)
