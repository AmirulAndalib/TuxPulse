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
- install apps from catalog
- bilingual interface: English / Romanian (in dev)

🚀 New Features

## UI
### Dashboard
<img width="1460" height="912" alt="v3 6-1" src="https://github.com/user-attachments/assets/3206f3a8-9d19-4a4c-ba38-09cf4634a5e3" />

### Maintenance
<img width="1460" height="912" alt="v3 6-2" src="https://github.com/user-attachments/assets/00803c70-55b9-4bff-9dfe-bbb5b4a5d40c" />

### Disk
<img width="1460" height="912" alt="v3 6-3" src="https://github.com/user-attachments/assets/caf95745-9d79-48be-af58-fa70e396a56a" />

### Kernel
<img width="1460" height="912" alt="v3 6-4" src="https://github.com/user-attachments/assets/a7bc40ee-075d-4888-943e-93941da8b7cf" />

### Cleaner
<img width="1460" height="912" alt="v3 6-5" src="https://github.com/user-attachments/assets/1d9b9d8e-f3e2-4efc-bccd-3fc466bfb30f" />

🧹 Improved Cleaner\

🔧 Unified Action System\
✔ Main button logically renamed: Run action\
✔ Functions integrated into the list:\
✔ Remove orphan packages\
✔ Vacuum journal (7 days)\

🧠 Smart Cleanup (cross-distro)\
✔ Debian/Ubuntu → apt autoremove\

### Startup
<img width="1460" height="912" alt="v3 6-6" src="https://github.com/user-attachments/assets/afe15be2-c5d0-48d4-8831-74667f7464c8" />

### Services
<img width="1460" height="912" alt="v3 6-7" src="https://github.com/user-attachments/assets/74fc3118-d9ec-474f-a6ef-a3c9414a910f" />

### Packages
<img width="1460" height="912" alt="v3 6-8" src="https://github.com/user-attachments/assets/11c97386-4e99-4fe2-a4b1-39acef0852e5" />

### Installer
<img width="1460" height="912" alt="v3 6-9" src="https://github.com/user-attachments/assets/92a59466-7bd7-448e-bf07-00c8a47cd47d" />

### About
<img width="1460" height="912" alt="v3 6-10" src="https://github.com/user-attachments/assets/57025642-5a71-4abe-8917-d97b4ef24b1a" />


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
