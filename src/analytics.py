import pandas as pd
import sqlite3
from src.database import DB_PATH

def get_category_roi_heatmap():
    """Generates data for Contradiction Density (ROI by Category)."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT category, AVG(predicted_profit_margin) as avg_margin, COUNT(id) as contradiction_volume
        FROM assets
        WHERE status IN ('New', 'Flagged')
        GROUP BY category
    """
    try:
        df = pd.read_sql_query(query, conn)
    except pd.errors.DatabaseError:
        df = pd.DataFrame(columns=['category', 'avg_margin', 'contradiction_volume'])
    conn.close()
    return df

def get_liquidity_pressure_stats():
    """Identifies the proportion of distressed sellers."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT liquidity_pressure, COUNT(id) as count
        FROM assets
        WHERE status IN ('New', 'Flagged')
        GROUP BY liquidity_pressure
    """
    try:
        df = pd.read_sql_query(query, conn)
    except pd.errors.DatabaseError:
        df = pd.DataFrame(columns=['liquidity_pressure', 'count'])
    conn.close()
    return df
