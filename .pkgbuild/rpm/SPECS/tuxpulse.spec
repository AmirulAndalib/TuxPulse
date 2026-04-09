Name:           tuxpulse
Version:        5.2
Release:        1%{?dist}
Summary:        Linux maintenance toolkit
License:        GPL-3.0-or-later
BuildArch:      noarch
Requires:       python3 python3-qt5 python3-psutil python3-matplotlib python3-matplotlib-qt5

%description
TuxPulse - Linux maintenance toolkit.

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
mkdir -p %{buildroot}%{_datadir}/tuxpulse

cp -a %{_sourcedir}/app %{buildroot}%{_datadir}/tuxpulse/

cat > %{buildroot}%{_bindir}/tuxpulse <<'LAUNCHER_EOF'
#!/usr/bin/env bash
exec python3 %{_datadir}/tuxpulse/app/main.py "$@"
LAUNCHER_EOF
chmod 755 %{buildroot}%{_bindir}/tuxpulse

cat > %{buildroot}%{_datadir}/applications/tuxpulse.desktop <<'DESKTOP_EOF'
[Desktop Entry]
Name=TuxPulse
GenericName=System Maintenance
Comment=Linux maintenance toolkit
Exec=tuxpulse
Icon=tuxpulse
Terminal=false
Type=Application
Categories=System;Utility;Settings;
StartupNotify=true
DESKTOP_EOF

if [ -f %{_sourcedir}/tuxpulse.png ]; then
    cp %{_sourcedir}/tuxpulse.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/
fi

%post
update-desktop-database %{_datadir}/applications || true
gtk-update-icon-cache %{_datadir}/icons/hicolor -f -q || true

%files
%{_bindir}/tuxpulse
%{_datadir}/applications/tuxpulse.desktop
%{_datadir}/icons/hicolor/256x256/apps/tuxpulse.png
%{_datadir}/tuxpulse

%changelog
* Thu Apr 09 2026 TuxPulse Team - 5.2-1
- Release v5.2
