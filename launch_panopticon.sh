#!/usr/bin/env bash
set -e

echo "[*] INITIATING PANOPTICON PROTOCOL V4 (Hyper-Local Wasatch Arbitrage)..."

# 1. Reload Systemd configuration
echo "[*] Reloading systemd user daemon..."
systemctl --user daemon-reload || echo "    [!] Systemd unavailable (Headless), continuing..."

# 2. Enable and Start the Service
echo "[*] Starting slc-arbitrage.service..."
systemctl --user enable --now slc-arbitrage.service || echo "    [!] Could not enable service, manual execution required."

echo "[*] System Armed."
echo "[*] To manually execute the station: uv run python main.py"
echo ""
echo "[*] Tailing journal for background extraction output (Ctrl+C to exit log view):"
# 3. Tail the log
journalctl --user -u slc-arbitrage.service -f || echo "    [!] Journalctl unavailable. Please run 'uv run python main.py' to observe logs."
