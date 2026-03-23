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

🚀 New Features

## UI
### Dashboard
<img width="1920" height="1040" alt="1" src="https://github.com/user-attachments/assets/89431438-fe6a-41e7-8ae3-fef1d54ce379" />

### Maintenance
<img width="1920" height="1040" alt="2" src="https://github.com/user-attachments/assets/c408c25a-de42-468b-b17b-e8242d3f8f64" />

### Disk
<img width="1920" height="1040" alt="3" src="https://github.com/user-attachments/assets/2441b5c1-09ce-4e2f-99f4-ddd8e43ec770" />

### Kernel
<img width="1920" height="1040" alt="4" src="https://github.com/user-attachments/assets/d26a6801-aeb1-49b1-8436-9c6c7de820ed" />


### Cleaner
<img width="1920" height="1040" alt="5" src="https://github.com/user-attachments/assets/052b667b-a925-4c3c-90c1-09e3af6269cc" />

🧹 Improved Cleaner\

🔧 Unified Action System\
✔ Main button logically renamed: Run action\
✔ Functions integrated into the list:\
✔ Remove orphan packages\
✔ Vacuum journal (7 days)\

🧠 Smart Cleanup (cross-distro)\
✔ Debian/Ubuntu → apt autoremove\

### Startup
<img width="1920" height="1040" alt="6" src="https://github.com/user-attachments/assets/0e19ea81-2886-4f6d-81fc-61f36919155b" />

### Services
<img width="1920" height="1040" alt="7" src="https://github.com/user-attachments/assets/a5c60a3b-bbd2-4e84-8052-8a90f930c0a2" />

### Packages
<img width="1920" height="1040" alt="8" src="https://github.com/user-attachments/assets/da4c468b-69be-4859-87ce-e8c97f548a28" />

### Installer
<img width="1920" height="1040" alt="9" src="https://github.com/user-attachments/assets/7de22a24-5b0d-4e21-bd43-18be992db99e" />


🛒 Fully integrated App Store\
Install apps by category (Browsers, Development, Multimedia, System Tools)\
Dual support:\
✔ Native packages (apt, pacman, dnf, zypper)\
✔ Flatpak (automatic fallback)\
✔ Live app search\
✔ Multiple installation (bulk install)\

🔄 Application Management\
✔ Install applications\
✔ Remove applications\
✔ Update individual applications\
✔ Bulk update\
✔ Detection of already installed applications\

🎯 Smart Source Selection\
✔ Automatic deactivation of “Native” if the application does not exist in the repository\
✔ Smart fallback to Flatpak\
✔ Avoid installation errors\

🔁 Auto Refresh UI\
Automatic refresh after:\
✔ install\
✔ remove\
✔ update\
Eliminates the need to restart the application\
Accurate real-time visual status\

🎨 Improved UI\
✔ Checkboxes visible in dark mode (white / light green)\
✔ Clearer interface for application selection\
✔ Dedicated buttons per application\

Language: [En]/[Ro]
<img width="1460" height="912" alt="switching-language" src="https://github.com/user-attachments/assets/3f5de768-2961-46e1-b519-1e3f811c98c0" />

🔐 Enterprise Architecture

🧱 Root Helper Service\
✔ Complete UI/root separation\
✔ Command execution via secure daemon\
✔ Removal of pkexec dependency\

🛡️ Security Hardening\
✔ Strict command validation\
✔ Controlled execution via package manager\
✔ Protection against unauthorized execution\

📜 Audit Logging\
Complete log:\
✔ user\
✔ executed command\
✔ output\
Location: /var/log/tuxpulse.log\

🧪 Improvements\
✔ Improved overall stability\
✔ Complete removal of scheduler (unstable across distros)\
✔ Reduced command execution errors\
✔ Better integration with Flatpak\

🐞 Bug Fixes\
✔ Fixed scheduler import crash\
✔ Fixed pkexec incompatibility with VSCode / container\
✔ Fixed Installer UI (incorrect button states)\
✔ Fixed invalid source selection\
✔ Fixed refresh after installation/uninstallation\
✔ Fixed dark mode checkbox visibility\

## Dependencies
Debian/Ubuntu
```bash
sudo apt install python3 python3-pyqt5 python3-psutil python3-matplotlib policykit-1 | policykid
```

## Run from source
Debian/Ubuntu
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
