#!/bin/bash
set -e

# ==============================================================================
# Physical Commodity Arbitrage Engine - Kali Linux Bootstrap
# ==============================================================================

echo "[*] Bootstrapping Physical Commodity Arbitrage Engine..."

# 1. Ensure system dependencies for Playwright and general compilation
echo "[*] Installing required system libraries (requires sudo)..."
sudo apt-get update -y
sudo apt-get install -y curl wget git python3-venv sqlite3 build-essential

# 2. Install 'uv' if not present
if ! command -v uv &> /dev/null; then
    echo "[*] Installing 'uv' package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL="/usr/local/bin" sh
else
    echo "[*] 'uv' is already installed."
fi

# 3. Create virtual environment using uv
echo "[*] Initializing uv virtual environment..."
uv venv .venv

# 4. Activate virtual environment and install dependencies
echo "[*] Installing project dependencies via uv..."
source .venv/bin/activate
uv pip install -e .

# 5. Install Playwright browsers (Chromium)
echo "[*] Installing Playwright Chromium browser for headless scraping..."
uv run playwright install chromium
uv run playwright install-deps

# 6. Initialize SQLite Database
echo "[*] Initializing SQLite database schema..."
uv run python -c "
import sqlite3
conn = sqlite3.connect('arbitrage_data.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        url TEXT UNIQUE NOT NULL,
        location TEXT,
        scraped_at TEXT NOT NULL,
        hardware_class TEXT,
        margin REAL DEFAULT NULL,
        shipping_cost REAL DEFAULT NULL,
        ebay_sold_price REAL DEFAULT NULL,
        processed BOOLEAN DEFAULT FALSE
    )
''')
conn.commit()
conn.close()
print('[+] Database initialized.')
"

# 7. Provide execution instructions
echo "====================================================================="
echo "[+] Bootstrap Complete. System is ready."
echo ""
echo "To operate the engine:"
echo "1. Activate environment: source .venv/bin/activate"
echo "2. Run Scraper: uv run python src/physical_commodity_arbitrage_engine/scraper.py"
echo "3. Run Calculator: uv run python src/physical_commodity_arbitrage_engine/arbitrage_calculator.py"
echo "4. Launch Dashboard: uv run streamlit run src/physical_commodity_arbitrage_engine/dashboard.py"
echo "====================================================================="

# Optional: Auto-launch dashboard
read -p "Do you want to launch the dashboard now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    uv run streamlit run src/physical_commodity_arbitrage_engine/dashboard.py
fi
