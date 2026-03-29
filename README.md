[![Group](https://img.shields.io/badge/Group-Telegram-blue?style=plastic)](https://t.me/tuxpulse)
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

![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/eoliann/TuxPulse/total?style=plastic)
![GitHub Downloads (specific asset, latest release)](https://img.shields.io/github/downloads/eoliann/TuxPulse/latest/tuxpulse.deb?displayAssetName=true&sort=date&style=plastic)
![GitHub Downloads (specific asset, all releases)](https://img.shields.io/github/downloads/eoliann/TuxPulse/tuxpulse.deb?displayAssetName=true&style=plastic)



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
- bilingual interface: English / Romanian (in dev)

🚀 New Features

## UI
### Dashboard
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Dashboard" src="https://github.com/user-attachments/assets/77037bc5-05bd-4b94-a160-4e2ec4d51988" />

### Maintenance
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Maintenance" src="https://github.com/user-attachments/assets/8595ed30-28e2-477c-991e-f82b43fb8fa6" />
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Maintenance-action" src="https://github.com/user-attachments/assets/823616a5-cfd0-4fb5-aeab-240c5d78b019" />
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Maintenance-done" src="https://github.com/user-attachments/assets/6b874707-5322-4a1c-b59c-57af42269758" />

### Disk
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Disk" src="https://github.com/user-attachments/assets/dbf2d18a-3358-4a65-9440-32ee9c864234" />

### Kernel
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Kernel" src="https://github.com/user-attachments/assets/8bc2d3d0-5f36-4835-986b-77511eaac4bf" />

### Cleaner
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Cleaner" src="https://github.com/user-attachments/assets/120a96fc-ade6-4de5-b26b-b669559e83be" />
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Cleaner-action" src="https://github.com/user-attachments/assets/aaa38d8c-6460-40b9-b824-547da4547b3a" />

🧹 Improved Cleaner\

🔧 Unified Action System\
✔ Main button logically renamed: Run action\
✔ Functions integrated into the list:\
✔ Remove orphan packages\
✔ Vacuum journal (7 days)\

🧠 Smart Cleanup (cross-distro)\
✔ Debian/Ubuntu → apt autoremove\

### Startup
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Startup-apps" src="https://github.com/user-attachments/assets/90c75265-da1c-4ac6-88a0-28c0155eb83d" />

### Services
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Services" src="https://github.com/user-attachments/assets/b3913d6b-18bd-46b2-8057-0ce2289bd29e" />

### Packages
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Packages" src="https://github.com/user-attachments/assets/504ecea0-994f-4ce2-8a12-0937e1dda791" />

### Installer
<img width="1920" height="1040" alt="TuxPulse - v3 4 - Installer" src="https://github.com/user-attachments/assets/b4aa64b0-b7bc-4049-8f7f-dc0bcae53562" />

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
