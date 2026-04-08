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

# TuxPulse

**TuxPulse** is a modern Linux maintenance toolkit with a PyQt desktop interface for updates, cleanup, monitoring, disk analysis, kernel cleanup suggestions, package inspection and application installation.

The project started with Debian/Ubuntu in mind, but the codebase is moving toward broader Linux support, especially for native package operations in the Installer and maintenance-related areas.

## What TuxPulse does

### System maintenance
- update system packages
- run upgrade and cleanup actions
- update Flatpak packages when Flatpak is installed
- launch grouped maintenance flows from a graphical interface

### Live monitoring dashboard
- CPU usage history
- RAM usage history
- disk usage history
- network activity history
- system summary panel

### Disk analysis
- root filesystem usage overview
- largest directories in the home folder
- largest files in the home folder

### Kernel tools
- detect current kernel
- list installed kernels
- suggest removable old kernels
- generate removal commands based on the detected package manager

### Cleaner
- thumbnail cache cleanup
- user cache cleanup
- trash cleanup
- temporary files cleanup
- journal vacuum
- orphan package cleanup

### Package tools
- list installed packages
- list upgradable packages
- remove packages
- purge packages

> Note: the package inspection/removal layer is currently strongest on Debian/Ubuntu systems.

### App installer
- categorized software catalog
- native package install/remove/update
- Flatpak install/remove/update
- native/Flatpak availability detection
- update detection for installed apps
- bulk actions
- live search
- automatic source selection with Flatpak fallback when needed

### System integration tabs
- startup applications viewer/editor
- system services viewer/manager
- About tab with project links and release check

### User experience
- English and Romanian interface
- dark mode and light mode
- sidebar navigation
- modern card-based UI

## Current support status

### Well covered today
- **Debian / Ubuntu**
  - source execution
  - DEB package build
  - privileged actions through packaged helper components

### Source execution already relevant
- **Fedora and other RPM-based distributions**
  - source execution is practical once the runtime dependencies are installed
  - parts of the app already include `dnf` / `rpm` logic

- **openSUSE and similar distributions**
  - source execution is practical once the runtime dependencies are installed
  - parts of the app already include `zypper` logic

### In progress / to be aligned further
- **Arch Linux**
  - parts of the codebase already include `pacman` logic
  - packaging and README instructions can be refined further as Arch support is finalized

## Dependencies

Install the runtime dependencies with your distro package manager.

### Debian / Ubuntu
```bash
sudo apt update
sudo apt install -y python3 python3-pyqt5 python3-psutil python3-matplotlib policykit-1
```

### Fedora / RPM-based
```bash
sudo dnf install -y python3 python3-qt5 python3-psutil python3-matplotlib polkit
```

### openSUSE
```bash
sudo zypper install -y python3 python3-qt5 python3-psutil python3-matplotlib polkit
```

### Arch Linux
```bash
sudo pacman -S --needed python python-pyqt5 python-psutil python-matplotlib polkit
```

### Optional but recommended
```bash
# for Flatpak app management inside TuxPulse
flatpak

# for service management tabs
systemd / systemctl
```

## Run from source

Clone the repository and run the application from the project root.

### Debian / Ubuntu
```bash
git clone https://github.com/eoliann/TuxPulse.git
cd TuxPulse
python3 app/main.py
```

### Fedora / RPM-based
```bash
git clone https://github.com/eoliann/TuxPulse.git
cd TuxPulse
python3 app/main.py
```

### openSUSE
```bash
git clone https://github.com/eoliann/TuxPulse.git
cd TuxPulse
python3 app/main.py
```

### Arch Linux
```bash
git clone https://github.com/eoliann/TuxPulse.git
cd TuxPulse
python app/main.py
```

## Build a DEB package

The repository already includes a dedicated DEB build script.

```bash
chmod +x build_deb.sh
./build_deb.sh
```

Expected result:
- a `.deb` package is created in the `dist/` directory
- the package version is read from `app/version.py`
- the build includes the application, helper files, systemd service and polkit policy

## RPM package build

At the moment, the public repository should document **source execution for RPM-based distributions**, but the README should **not pretend that an RPM package builder already exists** unless `build_rpm.sh` and the corresponding `.spec` file are committed.

A safe README position today is:
- source execution on Fedora / RPM-based systems is documented and supported as a development workflow
- native RPM packaging instructions will be added once the RPM build files are part of the repository

## Arch packaging

Arch support can be documented in two steps:
- source execution, which is already straightforward
- package build instructions, after the Arch packaging files and versioning are fully aligned

## Privileged operations

TuxPulse can use elevated privileges for administrative actions.

Depending on how it is started, this can involve:
- packaged helper components
- polkit integration
- `pkexec` or `sudo` fallback during source-based execution

## Project structure

```text
TuxPulse/
├── app/
│   ├── core/
│   ├── services/
│   ├── ui/
│   ├── main.py
│   ├── ui_main.py
│   └── version.py
├── helper/
├── packaging/
│   ├── deb/
│   ├── arch/
│   ├── polkit/
│   └── systemd/
└── build_deb.sh
```

## Notes

- Kernel cleanup should always be reviewed before removal.
- Service management requires `systemctl`.
- Flatpak operations are shown only when Flatpak is available.
- Running from source is the best path for development and testing across multiple distributions.
- DEB packaging is currently the packaging workflow that is clearly present in the public repository.

## About

- GitHub: https://github.com/eoliann/TuxPulse
- Releases: https://github.com/eoliann/TuxPulse/releases
- Issues: https://github.com/eoliann/TuxPulse/issues

TuxPulse is focused on giving Linux users a cleaner and more visual way to maintain their systems from one desktop application.
