import os
import shutil
import stat
import subprocess
import tempfile


def detect_package_manager():
    if shutil.which('apt'):
        return 'apt'
    if shutil.which('dnf'):
        return 'dnf'
    if shutil.which('pacman'):
        return 'pacman'
    if shutil.which('zypper'):
        return 'zypper'
    return None


def build_maintenance_commands():
    manager = detect_package_manager()
    commands = []
    if manager == 'apt':
        commands.extend([
            ('Update package lists', 'apt update'),
            ('Upgrade system packages', 'apt full-upgrade -y'),
            ('Remove unused packages', 'apt autoremove -y'),
            ('Clean package cache', 'apt autoclean'),
        ])
    elif manager == 'dnf':
        commands.extend([
            ('Upgrade system packages', 'dnf upgrade -y'),
            ('Remove unused packages', 'dnf autoremove -y'),
            ('Clean package cache', 'dnf clean all'),
        ])
    elif manager == 'pacman':
        commands.extend([
            ('Synchronize and upgrade packages', 'pacman -Syu --noconfirm'),
            ('Clean package cache', 'pacman -Sc --noconfirm'),
        ])
    elif manager == 'zypper':
        commands.extend([
            ('Upgrade system packages', 'zypper --non-interactive update'),
            ('Clean package cache', 'zypper clean'),
        ])
    if shutil.which('flatpak'):
        commands.append(('Update Flatpak packages', 'flatpak update -y'))
    return manager, commands


def _build_root_script(commands):
    lines = [
        '#!/usr/bin/env bash',
        'set -e',
        '',
        'log() { echo "__TP_LOG__$1"; }',
        'progress() { echo "__TP_PROGRESS__$1"; }',
        '',
        f'TOTAL={len(commands)}',
        'STEP=0',
        '',
    ]
    for title, command in commands:
        lines.extend([
            'STEP=$((STEP+1))',
            'PERCENT=$((STEP * 100 / TOTAL))',
            f'log "{title}"',
            f'log ">>> {command}"',
            command,
            'progress "$PERCENT"',
            '',
        ])
    lines.append('log "Full maintenance completed."')
    return '\n'.join(lines) + '\n'


def run_full_maintenance(log_callback, progress_callback):
    manager, commands = build_maintenance_commands()
    if manager is None:
        raise RuntimeError('No supported package manager found.')
    if not commands:
        raise RuntimeError('No maintenance commands available.')

    script_content = _build_root_script(commands)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.sh', encoding='utf-8') as tmp:
            tmp.write(script_content)
            temp_path = tmp.name
        os.chmod(temp_path, os.stat(temp_path).st_mode | stat.S_IXUSR)
        log_callback('Requesting administrator privileges...')
        process = subprocess.Popen(
            ['pkexec', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        if process.stdout is not None:
            for raw_line in process.stdout:
                line = raw_line.rstrip('\n')
                if line.startswith('__TP_LOG__'):
                    log_callback(line.replace('__TP_LOG__', '', 1))
                elif line.startswith('__TP_PROGRESS__'):
                    value = line.replace('__TP_PROGRESS__', '', 1).strip()
                    try:
                        progress_callback(int(value))
                    except ValueError:
                        log_callback(f'Invalid progress value: {value}')
                elif line.strip():
                    log_callback(line)
        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(f'Maintenance process failed with exit code {return_code}')
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
