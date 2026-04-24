import streamlit as st
import json
from pathlib import Path
from src.database import get_assets_by_status, get_all_assets, update_asset_status, update_asset_ledger, init_db
from src.manifest import generate_daily_manifest
from src.negotiator import generate_negotiation_template
from src.analytics import get_category_roi_heatmap
import plotly.express as px
import folium
from streamlit_folium import st_folium
import subprocess
import sys

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "targets.json"
LOG_FILE = BASE_DIR / "data" / "system.log"

st.set_page_config(page_title="Sovereign Command Center V4", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #C9D1D9; }
    .surplus-margin { color: #39FF14; font-weight: 900; font-size: 1.8rem; text-shadow: 0 0 10px #39FF14; }
    .asset-card { background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
    .distress-high { border-left: 5px solid #FF0000; }
    .free-loot { border: 2px solid #FF0000 !important; box-shadow: 0 0 20px #FF0000; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); } }
    a { color: #58A6FF !important; text-decoration: none; }
    .log-box { background-color: #000; color: #0f0; font-family: monospace; padding: 10px; height: 300px; overflow-y: scroll; border: 1px solid #333; }
    .roi-ticker { background-color: #000; color: #39FF14; font-size: 1.2rem; font-weight: bold; padding: 10px; border-bottom: 2px solid #333; margin-bottom: 20px; white-space: nowrap; overflow: hidden; box-sizing: border-box; }
</style>
""", unsafe_allow_html=True)

init_db()

# Calculate Live ROI Ticker
all_new = get_assets_by_status("New", limit=1000)
total_potential_surplus = all_new['surplus_margin'].sum() if not all_new.empty else 0.0
st.markdown(f'<div class="roi-ticker">LIVE ACTIVE ARBITRAGE SPREAD (WASATCH FRONT): ${total_potential_surplus:,.2f}</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("👁️ Command C&C")
    if st.button("Generate Strike Manifest", type="primary"):
        manifest_path = generate_daily_manifest()
        if manifest_path:
            st.success(f"Generated: {manifest_path.name}")
        else:
            st.warning("No flagged targets meet profitability floor.")

    if st.button("Force Scrape Trigger"):
        subprocess.Popen([sys.executable, "src/flip_scraper.py"])
        st.toast("Manual extraction initiated.")

    st.markdown("---")
    st.subheader("Technical Log Stream")
    logs = ""
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            logs = "".join(f.readlines()[-25:])
    st.markdown(f'<div class="log-box">{logs}</div>', unsafe_allow_html=True)

st.title("🖲️ SLC Arbitrage: Strike Station V4")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Asset Triage", "Strike Mode (Free Loot)", "Inventory Ledger", "Analytics", "Target Matrix"])

with tab1:
    assets = get_assets_by_status("New", limit=50)
    for index, row in assets.iterrows():
        # Enforce UI filtering for 15% ROI gating just in case
        if row['listed_price'] > (0.15 * row['intrinsic_value']):
            continue

        distress_class = "distress-high" if "Distress" in row['liquidity_pressure'] else ""

        with st.container():
            st.markdown(f'<div class="asset-card {distress_class}">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if row['image_url']: st.image(row['image_url'], use_column_width=True)
            with c2:
                gem_badge = "💎 HIDDEN GEM" if row['hidden_gem'] else ""
                st.subheader(f"{row['title']} {gem_badge}")
                st.markdown(f"**Listed:** ${row['listed_price']} | **AI Condition Score:** {row['condition_score']}/10")
                st.markdown(f"**Desperation Level:** {row['liquidity_pressure']}")
                st.markdown(f"> *{row['ai_notes']}*")
                st.markdown(f"[Proceed to Extraction]({row['url']})")

                with st.expander("One-Click Negotiator"):
                    templates = generate_negotiation_template(row['title'], row['listed_price'], row['seller_id'])
                    st.markdown("**Blitz:**")
                    st.code(templates["blitz"], language="text")
                    st.markdown("**Professional:**")
                    st.code(templates["professional"], language="text")

            with c3:
                st.markdown("ARBITRAGE SPREAD:")
                st.markdown(f"<span class='surplus-margin'>${row['surplus_margin']:.2f}</span>", unsafe_allow_html=True)
                if st.button("Flag for Manifest", key=f"flag_{row['id']}"):
                    update_asset_status(row['id'], "Flagged")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("Zero-Cost High-Yield Targets (Strike Mode)")
    free_assets = assets[(assets['listed_price'] == 0.0) & (assets['surplus_margin'] >= 100.0)]

    col_map, col_list = st.columns([1, 1])

    with col_map:
        m = folium.Map(location=[40.4950, -111.9391], zoom_start=10, tiles="CartoDB dark_matter")
        folium.Marker([40.4950, -111.9391], popup="HQ (Bluffdale)", icon=folium.Icon(color="blue", icon="home")).add_to(m)

        for index, row in free_assets.iterrows():
            if 'lat' in row and 'lon' in row and row['lat'] and row['lon']:
                folium.Marker([row['lat'], row['lon']], popup=f"${row['surplus_margin']} Profit", tooltip=row['title'], icon=folium.Icon(color="red", icon="warning")).add_to(m)
        st_folium(m, width=600, height=400)

    with col_list:
        if free_assets.empty:
            st.info("No critical free targets currently detected.")
        for index, row in free_assets.iterrows():
            with st.container():
                st.markdown('<div class="asset-card free-loot">', unsafe_allow_html=True)
                st.subheader(f"CRITICAL STRIKE: {row['title']}")
                st.markdown(f"**AI Condition:** {row['condition_score']}/10 | {row['ai_notes']}")
                st.markdown(f"**Desperation Level:** {row['liquidity_pressure']}")
                st.markdown(f"[Claim Item Now]({row['url']})")
                templates = generate_negotiation_template(row['title'], 0, row['seller_id'])
                st.code(templates["blitz"])
                st.markdown(f"<span class='surplus-margin'>+${row['surplus_margin']:.2f}</span>", unsafe_allow_html=True)
                if st.button("Flag for Manifest", key=f"strike_flag_{row['id']}"):
                    update_asset_status(row['id'], "Flagged")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.header("Financial Ledger & Inventory P&L")
    inv = get_all_assets()
    inv = inv[inv['status'].isin(["Flagged", "Contacted", "Purchased", "Refurbished", "Relisted", "Sold"])]

    if not inv.empty:
        st.dataframe(inv[['id', 'status', 'title', 'purchase_price', 'sale_price', 'gas_cost', 'repair_cost', 'realized_profit']])

        st.subheader("Update Ledger Entry")
        asset_to_update = st.selectbox("Select Asset ID", inv['id'].tolist())
        selected_row = inv[inv['id'] == asset_to_update].iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            new_status = st.selectbox("Status", ["Flagged", "Contacted", "Purchased", "Refurbished", "Relisted", "Sold"], index=["Flagged", "Contacted", "Purchased", "Refurbished", "Relisted", "Sold"].index(selected_row['status']))
            new_purchase = st.number_input("Purchase Price", value=float(selected_row['purchase_price']))
            new_sale = st.number_input("Sale Price", value=float(selected_row['sale_price']))
        with col2:
            new_gas = st.number_input("Gas Cost", value=float(selected_row['gas_cost']))
            new_repair = st.number_input("Repair Cost", value=float(selected_row['repair_cost']))
            new_time = st.number_input("Time Invested (Hrs)", value=float(selected_row['time_invested_hrs']))

        if st.button("Save Ledger Entry"):
            update_asset_ledger(asset_to_update, new_status, new_purchase, new_sale, new_gas, new_repair, new_time)
            st.success("Ledger Updated.")
            st.rerun()

with tab4:
    st.header("Contradiction Density")
    df_roi = get_category_roi_heatmap()
    if not df_roi.empty:
        fig = px.bar(df_roi, x='category', y='avg_margin', color='contradiction_volume', title="Average Profit Margin by Category (Density)", color_continuous_scale="Viridis")
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("Flippable Commodity Target Matrix")
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            config_data = json.load(f)

        updated_config = st.data_editor(config_data["targets"], num_rows="dynamic", use_container_width=True)
        if st.button("Save Configuration"):
            with open(CONFIG_PATH, "w") as f:
                json.dump({"targets": updated_config}, f, indent=4)
            st.success("Target Matrix Updated.")
