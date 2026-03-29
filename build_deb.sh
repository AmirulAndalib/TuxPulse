#!/usr/bin/env bash
set -euo pipefail

APP_NAME="tuxpulse"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_PKG_DIR="$ROOT_DIR/packaging/deb"
BUILD_ROOT="$ROOT_DIR/.pkgbuild"
PKG_DIR="$BUILD_ROOT/deb"
DIST_DIR="$ROOT_DIR/dist"
TARGET="$PKG_DIR/usr/share/tuxpulse"
VERSION_FILE="$ROOT_DIR/app/version.py"

if [[ ! -f "$VERSION_FILE" ]]; then
    echo "Missing version file: $VERSION_FILE" >&2
    exit 1
fi

VERSION="$(python3 - <<'PY' "$VERSION_FILE"
import re
import sys
from pathlib import Path

content = Path(sys.argv[1]).read_text(encoding='utf-8')
match = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
if not match:
    raise SystemExit(1)
print(match.group(1))
PY
)"

if [[ -z "$VERSION" ]]; then
    echo "Unable to read APP_VERSION from $VERSION_FILE" >&2
    exit 1
fi

rm -rf "$BUILD_ROOT" "$DIST_DIR"
mkdir -p "$PKG_DIR" "$DIST_DIR"

cp -a "$SRC_PKG_DIR/." "$PKG_DIR/"

rm -rf "$TARGET"
mkdir -p "$TARGET"

cp -a "$ROOT_DIR/app" "$TARGET/"
cp -a "$ROOT_DIR/helper" "$TARGET/"

find "$TARGET" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$TARGET" -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.txt' \) -delete

mkdir -p "$PKG_DIR/usr/lib/systemd/system"
cp "$ROOT_DIR/packaging/systemd/tuxpulse-helper.service" \
   "$PKG_DIR/usr/lib/systemd/system/tuxpulse-helper.service"

mkdir -p "$PKG_DIR/usr/share/polkit-1/actions"
cp "$ROOT_DIR/packaging/polkit/com.tuxpulse.policy" \
   "$PKG_DIR/usr/share/polkit-1/actions/com.tuxpulse.policy"

mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
if [[ -f "$ROOT_DIR/assets/tuxpulse.png" ]]; then
    cp "$ROOT_DIR/assets/tuxpulse.png" \
       "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/tuxpulse.png"
fi

cat > "$PKG_DIR/DEBIAN/postinst" <<'POST'
#!/usr/bin/env bash
set -e
systemctl daemon-reload || true
systemctl enable tuxpulse-helper.service || true
POST

find "$PKG_DIR/DEBIAN" -type d -exec chmod 755 {} +
find "$PKG_DIR/DEBIAN" -type f -exec chmod 644 {} +
[[ -f "$PKG_DIR/DEBIAN/postinst" ]] && chmod 755 "$PKG_DIR/DEBIAN/postinst"
[[ -f "$PKG_DIR/DEBIAN/preinst" ]] && chmod 755 "$PKG_DIR/DEBIAN/preinst"
[[ -f "$PKG_DIR/DEBIAN/prerm" ]] && chmod 755 "$PKG_DIR/DEBIAN/prerm"
[[ -f "$PKG_DIR/DEBIAN/postrm" ]] && chmod 755 "$PKG_DIR/DEBIAN/postrm"

find "$PKG_DIR" -type d -exec chmod 755 {} +
find "$PKG_DIR/usr/share/tuxpulse" -type f -exec chmod 644 {} +
[[ -f "$PKG_DIR/usr/bin/tuxpulse" ]] && chmod 755 "$PKG_DIR/usr/bin/tuxpulse"
[[ -f "$PKG_DIR/usr/share/tuxpulse/helper/tuxpulse_helper.py" ]] && chmod 755 "$PKG_DIR/usr/share/tuxpulse/helper/tuxpulse_helper.py"

OUTPUT="$DIST_DIR/${APP_NAME}_${VERSION}.deb"
dpkg-deb --build "$PKG_DIR" "$OUTPUT"
echo "Built: $OUTPUT"
