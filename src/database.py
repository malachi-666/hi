import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "slc_arbitrage_v3.db"

def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Core Assets Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            listed_price REAL NOT NULL,
            intrinsic_value REAL NOT NULL,
            predicted_profit_margin REAL NOT NULL,
            surplus_margin REAL NOT NULL,
            url TEXT UNIQUE NOT NULL,
            image_url TEXT,
            description TEXT,
            liquidity_pressure TEXT,
            resale_velocity TEXT,
            seller_id TEXT,
            lat REAL,
            lon REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'New'
        )
    ''')

    # Price History Table for Volatility Analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_url TEXT NOT NULL,
            observed_price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(asset_url) REFERENCES assets(url)
        )
    ''')

    conn.commit()
    return conn

def insert_asset(platform, category, title, listed_price, intrinsic_value, url,
                 image_url="", description="", liquidity_pressure="Normal",
                 resale_velocity="Medium", seller_id="Unknown", lat=None, lon=None):
    conn = init_db()
    cursor = conn.cursor()

    # Base Margin Calculations
    surplus_margin = intrinsic_value - listed_price
    # Simple ROI modeling: subtracting an estimated $10 for gas/time
    predicted_profit_margin = intrinsic_value - listed_price - 10.0

    inserted = False

    try:
        cursor.execute('''
            INSERT INTO assets (platform, category, title, listed_price, intrinsic_value,
                                predicted_profit_margin, surplus_margin, url, image_url,
                                description, liquidity_pressure, resale_velocity, seller_id, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (platform, category, title, listed_price, intrinsic_value,
              predicted_profit_margin, surplus_margin, url, image_url,
              description, liquidity_pressure, resale_velocity, seller_id, lat, lon))
        conn.commit()
        inserted = True
    except sqlite3.IntegrityError:
        # Asset exists, update its status and price history
        cursor.execute('''
            UPDATE assets SET listed_price = ?, timestamp = CURRENT_TIMESTAMP WHERE url = ?
        ''', (listed_price, url))
        conn.commit()
        inserted = False

    # Always log price history
    cursor.execute('''
        INSERT INTO price_history (asset_url, observed_price) VALUES (?, ?)
    ''', (url, listed_price))
    conn.commit()

    conn.close()
    return inserted

def get_assets_by_status(status="New", limit=50):
    conn = init_db()
    query = f"SELECT * FROM assets WHERE status = '{status}' ORDER BY predicted_profit_margin DESC LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_asset_status(asset_id, new_status):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE assets SET status = ? WHERE id = ?', (new_status, asset_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
