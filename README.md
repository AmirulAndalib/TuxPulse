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
<img width="1460" height="984" alt="v4 0-1" src="https://github.com/user-attachments/assets/38eacb07-dc99-405f-bca0-3b5328ff47b1" />

### Maintenance
<img width="1460" height="984" alt="v4 0-2" src="https://github.com/user-attachments/assets/cc783c5b-e9ed-4903-9838-a16fb5e36619" />

### Disk
<img width="1460" height="984" alt="v4 0-3" src="https://github.com/user-attachments/assets/c3717ec8-fc7c-453d-91ca-e193639a46e6" />
<img width="1460" height="984" alt="v4 0-3 1" src="https://github.com/user-attachments/assets/cc9b5a9c-99e2-4ed1-b6fb-536c5a22e5fb" />

### Kernel
<img width="1460" height="984" alt="v4 0-4" src="https://github.com/user-attachments/assets/3f01ff3d-eee7-4d40-88fd-8cf4ac21b1d7" />

### Cleaner
<img width="1460" height="984" alt="v4 0-5" src="https://github.com/user-attachments/assets/0ee51d72-df62-4677-a2aa-0e5409cd3a1d" />

🧹 Improved Cleaner\

🔧 Unified Action System\
✔ Main button logically renamed: Run action\
✔ Functions integrated into the list:\
✔ Remove orphan packages\
✔ Vacuum journal (7 days)\

🧠 Smart Cleanup (cross-distro)\
✔ Debian/Ubuntu → apt autoremove\

### Startup
<img width="1460" height="984" alt="v4 0-6" src="https://github.com/user-attachments/assets/1b843bee-1f66-4ebf-aba6-82de77318912" />

### Services
<img width="1460" height="984" alt="v4 0-7" src="https://github.com/user-attachments/assets/5f9a5f39-adb8-4f65-a68c-9979ec77ccda" />

### Packages
<img width="1460" height="984" alt="v4 0-8" src="https://github.com/user-attachments/assets/623aed24-9731-430f-8306-7abe85bbd3e1" />

### Installer
<img width="1460" height="984" alt="v4 0-9" src="https://github.com/user-attachments/assets/94526409-df32-426a-944d-ca782c75095c" />
<img width="1460" height="984" alt="v4 0-9 1" src="https://github.com/user-attachments/assets/09cb404c-a020-4243-80d0-1260ec0e07d4" />

### About
<img width="1460" height="984" alt="v4 0-10" src="https://github.com/user-attachments/assets/0b127ac8-f03b-4ce8-b9af-09230b818a17" />

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
✔ Dark Mode / Light Mode\
✔ Clearer interface for application selection\
✔ Dedicated buttons per application\

Language: [En]/[Ro]
<img width="1460" height="912" alt="switching-language" src="https://github.com/user-attachments/assets/3f5de768-2961-46e1-b519-1e3f811c98c0" />

Dark Mode / Light Mode
<img width="1460" height="984" alt="v4 0-1 1" src="https://github.com/user-attachments/assets/9ab07eb9-399f-4aff-b0dc-a24cc4de0e54" />

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
