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

# Copy to Tauri sidecar location (Windows)
if [ "$(uname)" != "Darwin" ]; then
  SIDECAR_DIR="src-tauri/binaries"
  mkdir -p "$SIDECAR_DIR"
  cp "build/backend/astro_nova_backend.exe" "$SIDECAR_DIR/backend-x86_64-pc-windows-gnu.exe"
  cp "build/backend/astro_nova_backend.exe" "$SIDECAR_DIR/backend-x86_64-pc-windows-msvc.exe"
  echo "[build_backend] Copied to $SIDECAR_DIR/"
fi

echo "[build_backend] Done → build/backend"
