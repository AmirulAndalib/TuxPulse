import os
import shutil
import subprocess
import tempfile
from pathlib import Path

TAG = '# TUXPULSE'


def _notify_command(task_name: str):
    if shutil.which('notify-send'):
        return f'notify-send "TuxPulse" "Task finished: {task_name}" || true'
    return 'true'


def _script_path(task_name: str):
    safe = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '-' for ch in task_name.strip() or 'task')
    return Path.home() / '.local' / 'bin' / f'tuxpulse-{safe}.sh'


def _build_script(profile: str, task_name: str, notify: bool):
    lines = ['#!/usr/bin/env bash', 'set -e', '']
    if profile == 'quick':
        lines.append('flatpak update -y || true')
    else:
        if shutil.which('apt'):
            lines.append('pkexec /bin/sh -c "apt update && apt full-upgrade -y && apt autoremove -y && apt autoclean" || true')
        elif shutil.which('dnf'):
            lines.append('pkexec /bin/sh -c "dnf upgrade -y && dnf autoremove -y && dnf clean all" || true')
        elif shutil.which('pacman'):
            lines.append('pkexec /bin/sh -c "pacman -Syu --noconfirm && pacman -Sc --noconfirm" || true')
        elif shutil.which('zypper'):
            lines.append('pkexec /bin/sh -c "zypper --non-interactive update && zypper clean" || true')
        lines.append('flatpak update -y || true')
    if notify:
        lines.append(_notify_command(task_name))
    return '\n'.join(lines) + '\n'


def _cron_expr(frequency: str, command: str):
    if frequency == 'daily':
        return f'0 9 * * * {command}'
    if frequency == 'weekly':
        return f'0 9 * * 1 {command}'
    return f'0 9 1 * * {command}'


def _read_current_crontab():
    try:
        return subprocess.check_output(['crontab', '-l'], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ''


def _write_crontab(content: str):
    with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as tmp:
        tmp.write(content)
        temp_name = tmp.name
    try:
        subprocess.check_call(['crontab', temp_name])
    finally:
        try:
            os.unlink(temp_name)
        except OSError:
            pass


def _parse_task_line(line: str):
    if TAG not in line:
        return None
    cron_part, _, meta = line.partition(TAG)
    cron_fields = cron_part.strip().split(maxsplit=5)
    if len(cron_fields) < 6:
        return None
    schedule = ' '.join(cron_fields[:5])
    command = cron_fields[5]
    meta = meta.strip()
    values = {}
    for part in meta.split(';'):
        if '=' in part:
            k, v = part.split('=', 1)
            values[k.strip()] = v.strip()
    name = values.get('name', Path(command).stem)
    frequency = values.get('frequency', 'daily')
    profile = values.get('profile', 'quick')
    notify = values.get('notify', 'yes') == 'yes'
    return {
        'name': name,
        'schedule': schedule,
        'command': command,
        'frequency': frequency,
        'profile': profile,
        'notify': notify,
        'line': line,
    }


def list_tasks():
    tasks = []
    for line in _read_current_crontab().splitlines():
        task = _parse_task_line(line)
        if task:
            tasks.append(task)
    return tasks


def get_current_schedule():
    lines = [task['line'] for task in list_tasks()]
    return '\n'.join(lines)


def save_task(task_name: str, profile: str, frequency: str, notify: bool):
    script_path = _script_path(task_name)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(_build_script(profile, task_name, notify), encoding='utf-8')
    script_path.chmod(0o755)

    current = _read_current_crontab().splitlines()
    filtered = []
    for line in current:
        task = _parse_task_line(line)
        if task and task['name'] == task_name:
            continue
        filtered.append(line)

    command = str(script_path)
    entry = _cron_expr(frequency, command)
    notify_value = 'yes' if notify else 'no'
    entry += f' {TAG} name={task_name};profile={profile};frequency={frequency};notify={notify_value}'
    filtered.append(entry)
    content = '\n'.join([line for line in filtered if line.strip()]) + '\n'
    _write_crontab(content)
    return True


def install_schedule(profile: str, frequency: str):
    return save_task('maintenance', profile, frequency, True)


def delete_task(task_name: str):
    current = _read_current_crontab().splitlines()
    filtered = []
    removed = False
    for line in current:
        task = _parse_task_line(line)
        if task and task['name'] == task_name:
            removed = True
            continue
        filtered.append(line)
    content = '\n'.join([line for line in filtered if line.strip()])
    if content:
        content += '\n'
    _write_crontab(content)
    return removed


def remove_schedule():
    return delete_task('maintenance')
