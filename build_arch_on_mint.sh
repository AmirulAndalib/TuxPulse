#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v podman >/dev/null 2>&1; then
  echo "ERROR: podman is not installed."
  echo "Install it on Linux Mint with:"
  echo "  sudo apt-get update && sudo apt-get install -y podman"
  exit 1
fi

pkgbuild_src=""
for candidate in \
  "$repo_root/PKGBUILD" \
  "$repo_root/PKGBUILD.tuxpulse" \
  "$repo_root/packaging/arch/PKGBUILD"; do
  if [[ -f "$candidate" ]]; then
    pkgbuild_src="$candidate"
    break
  fi
done

if [[ -z "$pkgbuild_src" ]]; then
  echo "ERROR: No PKGBUILD found."
  echo "Expected one of:"
  echo "  $repo_root/PKGBUILD"
  echo "  $repo_root/PKGBUILD.tuxpulse"
  echo "  $repo_root/packaging/arch/PKGBUILD"
  exit 1
fi

install_src=""
for candidate in \
  "$repo_root/tuxpulse.install" \
  "$repo_root/packaging/arch/tuxpulse.install"; do
  if [[ -f "$candidate" ]]; then
    install_src="$candidate"
    break
  fi
done

tmp_build="$(mktemp -d)"
trap 'rm -rf "$tmp_build"' EXIT

rsync -a \
  --exclude '.git' \
  --exclude 'dist' \
  --exclude '*.pkg.tar.zst' \
  "$repo_root/" "$tmp_build/TuxPulse/"

cp "$pkgbuild_src" "$tmp_build/TuxPulse/PKGBUILD"
if [[ -n "$install_src" ]]; then
  cp "$install_src" "$tmp_build/TuxPulse/tuxpulse.install"
fi

mkdir -p "$repo_root/dist"

podman run --rm \
  -v "$tmp_build/TuxPulse:/src:Z" \
  -v "$repo_root/dist:/dist:Z" \
  -w /src \
  docker.io/library/archlinux:latest \
  bash -lc '
    set -euo pipefail
    pacman -Syu --noconfirm
    pacman -S --needed --noconfirm base-devel rsync git python python-pyqt5 python-psutil python-matplotlib polkit desktop-file-utils

    useradd -m builder || true
    chown -R builder:builder /src /dist

    su builder -c "cd /src && makepkg -f --noconfirm"
    cp -v /src/*.pkg.tar.zst /dist/
  '

echo
echo "Build finished. Package(s):"
find "$repo_root/dist" -maxdepth 1 -type f -name '*.pkg.tar.zst' -print | sort
