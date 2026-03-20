![Followers](https://img.shields.io/github/followers/eoliann?style=plastic&color=green)
![Watchers](https://img.shields.io/github/watchers/eoliann/TuxPulse?style=plastic)
![Stars](https://img.shields.io/github/stars/eoliann/TuxPulse?style=plastic)
[![Donate](https://img.shields.io/badge/Donate-PayPal-blue?style=plastic)](https://www.paypal.com/donate/?hosted_button_id=PTH2EXUDS423S)
[![Donate](https://img.shields.io/badge/Donate-Revolut-8A2BE2?style=plastic)](http://revolut.me/adriannm9?style=plastic)

![Release Date](https://img.shields.io/github/release-date/eoliann/TuxPulse?style=plastic)
![Last Commit](https://img.shields.io/github/last-commit/eoliann/TuxPulse?style=plastic)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=plastic)](LICENSE.md)
![OS](https://img.shields.io/badge/OS-Linux-blue?style=plastic)
![Lang](https://img.shields.io/badge/Lang-Python-magenta?style=plastic)

![Total Downloads](https://img.shields.io/github/downloads/eoliann/TuxPulse/total?style=plastic)
![](https://img.shields.io/github/downloads/eoliann/TuxPulse/latest/tuxpulse.deb?displayAssetName=true&style=plastic&color=green)
[![Downloads latest](https://img.shields.io/github/downloads/eoliann/TuxPulse/latest/total?style=plastic)](https://github.com/eoliann/TuxPulse/releases/latest/download/tuxpulse.deb)


# TuxPulse

TuxPulse is a desktop maintenance toolkit for Debian/Ubuntu-based systems.

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

## UI
- Dashboard
<img width="1920" height="1040" alt="dashboard-en" src="https://github.com/user-attachments/assets/e46be026-ed5b-42d6-a042-9eba7f14688c" />
- Maintenance
<img width="1680" height="1050" alt="maintenance-en" src="https://github.com/user-attachments/assets/6c5a50dd-3853-4234-9c0c-bf6f2e3029ab" />
- Disk
<img width="1920" height="1040" alt="disk-en" src="https://github.com/user-attachments/assets/93d889c4-a295-4b87-ba0d-c79b311217de" />
- Kernel
<img width="1920" height="1040" alt="kernel-en" src="https://github.com/user-attachments/assets/96b6d8aa-904a-4955-889e-69b47689e55a" />
- Cleaner
<img width="1920" height="1040" alt="cleaner-en" src="https://github.com/user-attachments/assets/c77c2f9c-6cd2-4f66-a3b4-958b99c3fd5d" />
- Startup
<img width="1920" height="1040" alt="startup-en" src="https://github.com/user-attachments/assets/cafa3d53-2648-4fa8-92ca-7aaa807593d3" />
- Services
<img width="1920" height="1040" alt="services-en" src="https://github.com/user-attachments/assets/0e61fcc1-d648-49fe-8d0a-a4f64717f25d" />
- Packages
<img width="1920" height="1040" alt="packeges-en" src="https://github.com/user-attachments/assets/c7afb136-9bb3-4656-83ec-a3eebceeb05a" />
- Scheduler
<img width="1920" height="1040" alt="scheduler-en" src="https://github.com/user-attachments/assets/465590a5-4157-4bcd-8219-62f5c78ef0b1" />
Language: [En]/[Ro]
<img width="1460" height="912" alt="switching-language" src="https://github.com/user-attachments/assets/3f5de768-2961-46e1-b519-1e3f811c98c0" />

## Dependencies
Debian/Ubuntu
```bash
sudo apt install python3 python3-pyqt5 python3-psutil python3-matplotlib policykit-1 | policykid
```
Arch
```bash
sudo pacman -S python python-pyqt5 python-psutil python-matplotlib polkit
```

## Run from source
Debian/Ubuntu
```bash
python3 app/main.py
```
Arch
```bash
python app/main.py
```

## Build .deb
```bash
chmod +x build_deb.sh
./build_deb.sh
```

## Notes
- Administrative actions use `pkexec`.
- Scheduled tasks use the current user's `crontab` and writes a per-user crontab entry..
- Kernel cleanup removes only the packages suggested by the built-in analyzer. Review them before deletion.
- Full Maintenance uses a single `pkexec` session, so the admin password should be requested once.
- Startup and Services tabs are read-only in this preview.
- Cleaner can wipe user cache targets directly and root targets through pkexec.



## Custom icon
Place your PNG icon here before building:

```bash
assets/tuxpulse.png
```

The build script copies it to:

```bash
packaging/deb/usr/share/icons/hicolor/256x256/apps/tuxpulse.png
```
