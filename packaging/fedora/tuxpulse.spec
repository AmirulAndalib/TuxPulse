Name: tuxpulse
Version: 2.0
Release: 1%{?dist}
Summary: Multi-distro Linux maintenance and installer toolkit
License: MIT
BuildArch: noarch
Requires: python3, python3-qt5, python3-psutil, python3-matplotlib, polkit
Recommends: flatpak

%description
TuxPulse provides maintenance, cleanup, package management and a software installer UI.

%install
mkdir -p %{buildroot}/usr/share/tuxpulse
cp -r app %{buildroot}/usr/share/tuxpulse/
cp -r helper %{buildroot}/usr/share/tuxpulse/
mkdir -p %{buildroot}/usr/bin
cp packaging/deb/usr/bin/tuxpulse %{buildroot}/usr/bin/tuxpulse
mkdir -p %{buildroot}/usr/lib/systemd/system
cp packaging/systemd/tuxpulse-helper.service %{buildroot}/usr/lib/systemd/system/tuxpulse-helper.service
mkdir -p %{buildroot}/usr/share/polkit-1/actions
cp packaging/polkit/com.tuxpulse.policy %{buildroot}/usr/share/polkit-1/actions/com.tuxpulse.policy

%files
/usr/share/tuxpulse
/usr/bin/tuxpulse
/usr/lib/systemd/system/tuxpulse-helper.service
/usr/share/polkit-1/actions/com.tuxpulse.policy
