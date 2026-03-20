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
<img width="1920" height="1040" alt="1" src="https://github.com/user-attachments/assets/02de4d0e-fee8-4827-b9a6-e1eb3a1c9cf4" />

### Maintenance
<img width="1920" height="1040" alt="2" src="https://github.com/user-attachments/assets/66880bfd-4f69-4306-a358-881b193c8fe6" />
<img width="1920" height="1040" alt="2 1" src="https://github.com/user-attachments/assets/3a1453cb-3606-47be-be3a-3e738e3ede90" />
<img width="1920" height="1040" alt="2 2" src="https://github.com/user-attachments/assets/ff51afe6-b38d-473b-b042-a1374d0c07a0" />

### Disk
<img width="1920" height="1040" alt="3" src="https://github.com/user-attachments/assets/ebd3c3b4-c758-4dc6-b566-07df2b68fdab" />

### Kernel
<img width="1920" height="1040" alt="4" src="https://github.com/user-attachments/assets/bb2fa5fe-1858-432b-bb4d-e2590e381f05" />

### Cleaner
<img width="1920" height="1040" alt="5 0" src="https://github.com/user-attachments/assets/65636407-4fe4-450b-be74-22adab9fb60d" />
<img width="1920" height="1040" alt="5 1" src="https://github.com/user-attachments/assets/3ae21d62-e3d0-4912-97c8-e2563595dbe3" />
<img width="1920" height="1040" alt="5 2" src="https://github.com/user-attachments/assets/4cb0d6e8-5181-4649-8710-ea7dd3f797a1" />
<img width="1920" height="1040" alt="5 3" src="https://github.com/user-attachments/assets/38e42a8f-da3a-4473-8c8b-edb34abc84a3" />
<img width="1920" height="1040" alt="5 4" src="https://github.com/user-attachments/assets/782ea3aa-ebde-47f5-b99d-22f0582ef097" />

🧹 Improved Cleaner\

🔧 Unified Action System\
✔ Main button logically renamed: Run action\
✔ Functions integrated into the list:\
✔ Remove orphan packages\
✔ Vacuum journal (7 days)\

🧠 Smart Cleanup (cross-distro)\
✔ Debian/Ubuntu → apt autoremove\
✔ Arch → orphan package detection\
✔ Fedora → dnf autoremove\
✔ openSUSE → zypper clean deps\

### Startup
<img width="1920" height="1040" alt="6" src="https://github.com/user-attachments/assets/6eb508fc-dec1-4d56-9bcc-1945bd03f4a9" />

### Services
<img width="1920" height="1040" alt="7" src="https://github.com/user-attachments/assets/6eb3c8b7-212a-43d4-bad9-4278562804c6" />

### Packages
<img width="1920" height="1040" alt="8" src="https://github.com/user-attachments/assets/b7002b69-2eba-4861-aebe-74a16fca6468" />

### Installer
<img width="1920" height="1040" alt="9" src="https://github.com/user-attachments/assets/29292129-3cd0-40ab-9db7-928364ffe2eb" />
<img width="1460" height="912" alt="9 1" src="https://github.com/user-attachments/assets/3f76d23f-636f-49ee-a747-60d4121cc1cd" />
<img width="1460" height="912" alt="9 2" src="https://github.com/user-attachments/assets/44d1884a-633f-483c-ab2d-212a3f465016" />

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

⚙️ Cross-Distro Compatibility\
Full support for:\
✔ Debian / Ubuntu\
✔ Arch Linux\
✔ Fedora\
✔ openSUSE\

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
Arch
```bash
sudo pacman -S python python-pyqt5 python-psutil python-matplotlib polkit flatpak
```
Fedora
```bash
sudo dnf install python3 python3-qt5 python3-psutil python3-matplotlib python3-matplotlib-qt5 polkit flatpak
```
openSUSE
```bash
sudo zypper install python3 python3-qt5 python3-psutil python3-matplotlib polkit flatpak
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
