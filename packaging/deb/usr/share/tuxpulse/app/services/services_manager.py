import shutil
import subprocess


STATE_RUNNING = 'Running'
STATE_STOPPED = 'Stopped'
STATE_DISABLED = 'Disabled'
STATE_ENABLED = 'Enabled'


def _active_map():
    mapping = {}
    if not shutil.which('systemctl'):
        return mapping
    try:
        output = subprocess.check_output(
            ['systemctl', 'list-units', '--type=service', '--all', '--no-pager', '--no-legend'],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return mapping
    for line in output.splitlines():
        parts = line.split(None, 4)
        if len(parts) >= 4:
            mapping[parts[0]] = parts[2]
    return mapping


def list_services(limit=200):
    if not shutil.which('systemctl'):
        return []
    active = _active_map()
    try:
        output = subprocess.check_output(
            ['systemctl', 'list-unit-files', '--type=service', '--no-pager', '--no-legend'],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    services = []
    for line in output.splitlines()[:limit]:
        parts = line.split()
        if len(parts) >= 2:
            name, unit_state = parts[0], parts[1]
            active_state = active.get(name, 'inactive')
            if unit_state == 'disabled':
                state = STATE_DISABLED
            elif active_state == 'active':
                state = STATE_RUNNING
            elif unit_state == 'enabled':
                state = STATE_STOPPED
            else:
                state = STATE_ENABLED if unit_state == 'enabled' else STATE_STOPPED
            services.append({
                'name': name,
                'state': state,
                'unit_state': unit_state,
                'active_state': active_state,
            })
    return services


def set_service_state(service_name: str, desired_state: str):
    if not shutil.which('systemctl'):
        raise RuntimeError('systemctl is not available.')

    if desired_state == STATE_RUNNING:
        commands = [
            ['pkexec', 'systemctl', 'enable', service_name],
            ['pkexec', 'systemctl', 'start', service_name],
        ]
    elif desired_state == STATE_STOPPED:
        commands = [
            ['pkexec', 'systemctl', 'stop', service_name],
        ]
    elif desired_state == STATE_DISABLED:
        commands = [
            ['pkexec', 'systemctl', 'stop', service_name],
            ['pkexec', 'systemctl', 'disable', service_name],
        ]
    else:
        raise RuntimeError(f'Unsupported service state: {desired_state}')

    for cmd in commands:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stdout.strip() or f'Failed to run: {" ".join(cmd)}')
    return True
