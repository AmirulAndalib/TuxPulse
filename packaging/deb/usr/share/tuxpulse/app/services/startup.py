from configparser import ConfigParser
from pathlib import Path


def _desktop_paths():
    return [Path.home() / '.config' / 'autostart', Path('/etc/xdg/autostart')]


def _read_desktop_entry(desktop: Path):
    cp = ConfigParser(interpolation=None)
    cp.optionxform = str
    cp.read(desktop, encoding='utf-8')
    section = cp['Desktop Entry']
    return cp, section


def list_startup_apps():
    apps = []
    for base in _desktop_paths():
        if not base.exists():
            continue
        for desktop in sorted(base.glob('*.desktop')):
            try:
                _, section = _read_desktop_entry(desktop)
                apps.append({
                    'name': section.get('Name', desktop.stem),
                    'exec': section.get('Exec', ''),
                    'enabled': section.get('Hidden', 'false').lower() != 'true',
                    'path': str(desktop),
                    'scope': 'user' if str(base).startswith(str(Path.home())) else 'system',
                })
            except Exception:
                continue
    return apps


def set_startup_enabled(path: str, enabled: bool):
    desktop = Path(path)
    if not desktop.exists():
        raise RuntimeError('Startup entry not found.')
    if not str(desktop).startswith(str(Path.home())):
        raise RuntimeError('Only user startup entries can be changed from TuxPulse preview.')

    cp, section = _read_desktop_entry(desktop)
    section['Hidden'] = 'false' if enabled else 'true'
    desktop.parent.mkdir(parents=True, exist_ok=True)
    with desktop.open('w', encoding='utf-8') as fh:
        cp.write(fh)
    return True
