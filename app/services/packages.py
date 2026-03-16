import shutil
import subprocess


def _apt_list_installed(search='', limit=300):
    output = subprocess.check_output(['dpkg-query', '-W', '-f=${Package}\t${Version}\n'], text=True)
    items = []
    search_lower = search.lower().strip()
    for line in output.splitlines():
        pkg, _, ver = line.partition('\t')
        if search_lower and search_lower not in pkg.lower():
            continue
        items.append({'name': pkg, 'version': ver, 'status': 'installed'})
        if limit is not None and len(items) >= limit:
            break
    return items


def _rpm_list_installed(search='', limit=300):
    output = subprocess.check_output(['rpm', '-qa', '--qf', '%{NAME}\t%{VERSION}-%{RELEASE}\n'], text=True)
    items = []
    search_lower = search.lower().strip()
    for line in output.splitlines():
        pkg, _, ver = line.partition('\t')
        if search_lower and search_lower not in pkg.lower():
            continue
        items.append({'name': pkg, 'version': ver, 'status': 'installed'})
        if limit is not None and len(items) >= limit:
            break
    return items


def list_installed_packages(limit=300, search=''):
    try:
        if shutil.which('dpkg-query'):
            return _apt_list_installed(search=search, limit=limit)
        if shutil.which('rpm'):
            return _rpm_list_installed(search=search, limit=limit)
    except Exception:
        return []
    return []


def count_installed_packages():
    try:
        if shutil.which('dpkg-query'):
            output = subprocess.check_output(['dpkg-query', '-W', '-f=${Package}\n'], text=True)
            return len([line for line in output.splitlines() if line.strip()])
        if shutil.which('rpm'):
            output = subprocess.check_output(['rpm', '-qa'], text=True)
            return len([line for line in output.splitlines() if line.strip()])
    except Exception:
        return 0
    return 0


def list_upgradable_packages(limit=300):
    if shutil.which('apt'):
        try:
            output = subprocess.check_output(['apt', 'list', '--upgradable'], text=True, stderr=subprocess.DEVNULL)
            items = []
            for line in output.splitlines():
                if '/' not in line or 'Listing...' in line:
                    continue
                name = line.split('/', 1)[0]
                version = line.split()[1] if len(line.split()) > 1 else 'upgradable'
                items.append({'name': name, 'version': version, 'status': 'upgradable'})
                if limit is not None and len(items) >= limit:
                    break
            return items
        except Exception:
            return []
    return []


def _run_pkg_command(cmd, ok_message):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or f'Failed to run: {" ".join(cmd)}')
    return result.stdout.strip() or ok_message


def remove_package(name: str):
    if shutil.which('apt'):
        return _run_pkg_command(['pkexec', 'apt', 'remove', '-y', name], f'Package {name} removed.')
    if shutil.which('dnf'):
        return _run_pkg_command(['pkexec', 'dnf', 'remove', '-y', name], f'Package {name} removed.')
    if shutil.which('pacman'):
        return _run_pkg_command(['pkexec', 'pacman', '-R', '--noconfirm', name], f'Package {name} removed.')
    if shutil.which('zypper'):
        return _run_pkg_command(['pkexec', 'zypper', '--non-interactive', 'remove', name], f'Package {name} removed.')
    raise RuntimeError('No supported package manager found.')


def purge_package(name: str):
    if shutil.which('apt'):
        return _run_pkg_command(['pkexec', 'apt', 'purge', '-y', name], f'Package {name} purged.')
    return remove_package(name)
