# TuxPulse v1.0

DebCare is a desktop maintenance toolkit for Debian/Ubuntu-based systems.

## Main features
- System update
- System cleanup
- Flatpak package update
- systemd logs cleanup
- thumbnail cleanup
- live monitoring dashboard
- modern graphical disk analysis
- kernel analysis and suggested old-kernel removal
- task scheduler based on user crontab
- bilingual interface: English / Romanian

## Dependencies
```bash
sudo apt install python3 python3-pyqt5 python3-psutil python3-matplotlib policykit-1
```

## Run from source
```bash
python3 app/main.py
```

## Build .deb
```bash
chmod +x build_deb.sh
./build_deb.sh
```

## Notes
- Administrative actions use `pkexec`.
- Scheduled tasks use the current user's `crontab`.
- Kernel cleanup removes only the packages suggested by the built-in analyzer. Review them before deletion.


## Custom icon
Place your PNG icon here before building:

```bash
assets/tuxpulse.png
```

The build script copies it to:

```bash
packaging/deb/usr/share/icons/hicolor/256x256/apps/tuxpulse.png
```
