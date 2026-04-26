import streamlit as st
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from outreach_generator import generate_pitch

load_dotenv()

st.set_page_config(page_title="Physical Commodity Arbitrage", layout="wide", page_icon="📡")

# Custom CSS for a slightly darker/cleaner terminal-ish look if desired
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    conn = sqlite3.connect("arbitrage_data.db")
    try:
        df = pd.read_sql_query("SELECT * FROM listings ORDER BY margin DESC", conn)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        df = pd.DataFrame()
    conn.close()
    return df

st.title("📡 Physical Commodity Arbitrage Engine")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Configuration")
default_zip = os.getenv("DEFAULT_ZIP", "84088")
default_radius = int(os.getenv("DEFAULT_RADIUS", "50"))

target_zip = st.sidebar.text_input("Target Zip Code", value=default_zip)
search_radius = st.sidebar.slider("Sweep Radius (miles)", min_value=5, max_value=200, value=default_radius)

st.sidebar.markdown("---")
if st.sidebar.button("Run Scraper"):
    st.sidebar.info("Triggering scraper... (Run via CLI for full async performance)")
    # In a fully deployed version, this could trigger the async script via subprocess

if st.sidebar.button("Calculate Margins"):
    st.sidebar.info("Triggering arbitrage calculator... (Run via CLI for full async performance)")

# --- MAIN DASHBOARD ---
df = load_data()

if df.empty:
    st.warning("No data found in local database. Run scraper and calculator.")
else:
    # Filter out null margins or un-processed items
    df_processed = df[df['processed'] == 1].copy()

    if df_processed.empty:
         st.info("Data scraped but not yet processed. Run arbitrage calculator.")
         st.dataframe(df)
    else:
        # Display Top Targets
        st.subheader("High-Margin Targets")
        top_targets = df_processed[df_processed['margin'] > 0].sort_values(by="margin", ascending=False)

        # Format currency columns for display
        display_df = top_targets[['id', 'title', 'location', 'hardware_class', 'price', 'ebay_sold_price', 'shipping_cost', 'margin', 'source', 'url']]
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
        display_df['ebay_sold_price'] = display_df['ebay_sold_price'].apply(lambda x: f"${x:,.2f}")
        display_df['shipping_cost'] = display_df['shipping_cost'].apply(lambda x: f"${x:,.2f}")
        display_df['margin'] = display_df['margin'].apply(lambda x: f"${x:,.2f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Outreach Generator")

        col1, col2 = st.columns([1, 2])

        with col1:
             selected_id = st.selectbox("Select Target ID for Outreach", options=top_targets['id'].tolist())

        with col2:
             if selected_id:
                 target_row = top_targets[top_targets['id'] == selected_id].iloc[0]
                 pitch = generate_pitch(target_row['title'], target_row['hardware_class'], target_row['price'])
                 st.text_area("Negotiation Script (Copy/Paste ready)", value=pitch, height=250)
                 st.markdown(f"**Target URL:** [Link]({target_row['url']})")
