#!/usr/bin/env bash
set -e

APP_NAME="tuxpulse"
VERSION="3.0"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$ROOT_DIR/packaging/deb"
DIST_DIR="$ROOT_DIR/dist"
TARGET="$PKG_DIR/usr/share/tuxpulse"

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
rm -rf "$TARGET"
mkdir -p "$TARGET"

cp -r "$ROOT_DIR/app" "$TARGET/"
cp -r "$ROOT_DIR/helper" "$TARGET/"

mkdir -p "$PKG_DIR/usr/lib/systemd/system"
cp "$ROOT_DIR/packaging/systemd/tuxpulse-helper.service" "$PKG_DIR/usr/lib/systemd/system/tuxpulse-helper.service"
mkdir -p "$PKG_DIR/usr/share/polkit-1/actions"
cp "$ROOT_DIR/packaging/polkit/com.tuxpulse.policy" "$PKG_DIR/usr/share/polkit-1/actions/com.tuxpulse.policy"

mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
if [ -f "$ROOT_DIR/assets/tuxpulse.png" ]; then
    cp "$ROOT_DIR/assets/tuxpulse.png" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/tuxpulse.png"
fi

cat > "$PKG_DIR/DEBIAN/postinst" <<'POST'
#!/usr/bin/env bash
set -e
systemctl daemon-reload || true
systemctl enable tuxpulse-helper.service || true
POST
chmod 755 "$PKG_DIR/DEBIAN/postinst"
chmod 755 "$PKG_DIR/usr/bin/tuxpulse"

dpkg-deb --build "$PKG_DIR" "$DIST_DIR/${APP_NAME}_${VERSION}_all.deb"
echo "Built: $DIST_DIR/${APP_NAME}_${VERSION}_all.deb"
