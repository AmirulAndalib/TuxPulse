#!/usr/bin/env bash
set -e
APPID=ro.eoliann.TuxPulse
flatpak-builder --force-clean build-dir flatpak/$APPID.json
flatpak build-export repo build-dir
flatpak build-bundle repo tuxpulse.flatpak $APPID
echo "Flatpak build complete: tuxpulse.flatpak"
