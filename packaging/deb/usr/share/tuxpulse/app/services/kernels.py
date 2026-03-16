import os
import platform
import re
import shutil
import subprocess


_VERSION_RE = re.compile(r'^(linux-image|kernel-default)-(.+)$')


def _run_output(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ''


def get_kernel_report():
    current = platform.release()
    installed = []
    suggested = []

    if shutil.which('dpkg'):
        output = _run_output(['dpkg-query', '-W', '-f=${Package}\n'])
        for line in output.splitlines():
            if line.startswith('linux-image-'):
                installed.append(line.replace('linux-image-', ''))
    elif shutil.which('rpm'):
        output = _run_output(['rpm', '-qa'])
        for line in output.splitlines():
            if 'kernel' in line:
                installed.append(line)

    if not installed:
        installed = [current]

    for item in installed:
        if current not in item:
            suggested.append(item)

    return {
        'current': current,
        'installed': installed,
        'suggested': suggested,
    }


def removal_commands_for_suggested():
    report = get_kernel_report()
    cmds = []
    if shutil.which('apt'):
        for kernel in report['suggested']:
            pkg = kernel if kernel.startswith('linux-image-') else f'linux-image-{kernel}'
            cmds.append(['apt', 'purge', '-y', pkg])
    elif shutil.which('dnf'):
        for kernel in report['suggested']:
            cmds.append(['dnf', 'remove', '-y', kernel])
    elif shutil.which('zypper'):
        for kernel in report['suggested']:
            cmds.append(['zypper', '--non-interactive', 'remove', kernel])
    return cmds
