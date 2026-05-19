#!/usr/bin/env bash
set -e

# Platform-aware PyInstaller backend build
# macOS → pyinstaller-mac.spec (Unix executable)
# other  → pyinstaller.spec       (Windows .exe)

SPEC="build/pyinstaller.spec"
if [ "$(uname)" = "Darwin" ]; then
  SPEC="build/pyinstaller-mac.spec"
fi

echo "[build_backend] Using spec: $SPEC"
pyinstaller "$SPEC" --noconfirm 2>&1 | tail -1

# Replace build/backend with freshly built output
rm -rf build/backend
cp -r dist/astro_nova_backend build/backend
echo "[build_backend] Done → build/backend"
