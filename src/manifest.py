import qrcode
import pandas as pd
import math
from pathlib import Path
from src.database import get_assets_by_status
import datetime
import base64
from io import BytesIO

BASE_DIR = Path(__file__).parent.parent
MANIFEST_DIR = BASE_DIR / "manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

# Bluffdale, UT coordinates
BLUFFDALE_LAT = 40.4950
BLUFFDALE_LON = -111.9391

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in miles between two points."""
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return 999.0 # Sort missing locations to the bottom

    R = 3958.8 # Earth radius in miles
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def generate_qr_base64(url):
    qr = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

def generate_daily_manifest():
    df = get_assets_by_status("New", limit=200)
    if df.empty: return None

    # 1. The $100 Floor
    df = df[df['surplus_margin'] >= 100.0].copy()
    if df.empty: return None

    # 2. Geospatial Prioritization
    if 'lat' in df.columns and 'lon' in df.columns:
        df['distance_miles'] = df.apply(lambda row: haversine(row['lat'], row['lon'], BLUFFDALE_LAT, BLUFFDALE_LON), axis=1)
        # Sort by Free first, then distance, then profit
        df = df.sort_values(by=['listed_price', 'distance_miles', 'predicted_profit_margin'], ascending=[True, True, False])
    else:
        df = df.sort_values(by=['listed_price', 'predicted_profit_margin'], ascending=[True, False])

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    manifest_path = MANIFEST_DIR / "daily_strike.md"

    with open(manifest_path, "w") as f:
        f.write(f"# 🏴‍☠️ SLC Strike Manifest: {date_str}\n\n")
        f.write("## ⚠️ CRITICAL TARGETS (Floor: $100+ Surplus)\n\n")

        for index, row in df.iterrows():
            dist_str = f"({row['distance_miles']:.1f} miles from Bluffdale)" if 'distance_miles' in df.columns and row['distance_miles'] < 900 else ""
            qr_b64 = generate_qr_base64(row['url'])

            f.write(f"### [ ] {row['title']} | {row['platform']}\n")
            f.write(f"- **Price:** ${row['listed_price']:.2f} | **Profit:** ${row['predicted_profit_margin']:.2f}\n")
            f.write(f"- **Liquidity Pressure:** {row['liquidity_pressure']} {dist_str}\n")
            f.write(f"- **URL:** [Open Listing]({row['url']})\n")
            f.write(f"![QR Code]({qr_b64})\n")
            f.write("\n---\n")

    return manifest_path
