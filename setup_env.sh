#!/usr/bin/env bash
set -e

echo "[*] Initializing Panopticon Protocol V3 Environment..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "[*] Please install uv manually: curl -LsSf https://astral.sh/uv/install.sh | bash"
else
    echo "[*] Syncing dependencies via uv..."
    uv sync
    echo "[*] Installing Chromium for Playwright..."
    uv run playwright install chromium
fi

# Create directory structure
echo "[*] Constructing filesystem layout..."
mkdir -p data manifests config logs

# Audio trigger check
AUDIO_PATH="/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"
if [ ! -f "$AUDIO_PATH" ]; then
    echo "[!] WARNING: System audio trigger not found at $AUDIO_PATH."
    echo "    (If on Debian/Kali, ensure sound-theme-freedesktop is installed)."
else
    echo "[*] Audio trigger verified."
fi

echo "[*] Setup complete. Station is ready for Launch."
