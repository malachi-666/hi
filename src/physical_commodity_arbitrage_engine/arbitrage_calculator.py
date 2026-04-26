import asyncio
import sqlite3
import random
from typing import List, Dict, Any, Tuple
from playwright.async_api import async_playwright, Page
from loguru import logger
import re
import urllib.parse

# Hardcoded flat-rate dictionary based on hardware class
SHIPPING_COSTS = {
    "Components": 5.00,
    "Laptop": 15.00,
    "General Electronics": 20.00,
    "Heavy Infrastructure": 0.00 # Freight/Local Repo Only
}

async def stealth_delay(min_ms: int = 1000, max_ms: int = 3000):
    delay = random.uniform(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)

async def scrape_ebay_sold_price(page: Page, item_title: str) -> float:
    # Aggressive Playwright web-scraping approach for eBay's "completed/sold" listings
    # Clean the title slightly for better search results (e.g. remove generic terms)
    search_term = urllib.parse.quote(item_title[:50]) # eBay might choke on very long strings
    url = f"https://www.ebay.com/sch/i.html?_nkw={search_term}&LH_Complete=1&LH_Sold=1"

    logger.debug(f"Querying eBay Sold for: {item_title[:50]}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await stealth_delay(2000, 5000)

        # Extract prices from the first few listings
        prices = []
        items = await page.query_selector_all(".s-item__price")

        for item in items[:5]: # Take top 5 recent sold items to average
            text = await item.inner_text()
            # Handle ranges like "$10.00 to $15.00" by taking the lower bound
            match = re.search(r'\$?([\d,]+\.\d{2})', text)
            if match:
                price_val = float(match.group(1).replace(',', ''))
                prices.append(price_val)

        if prices:
            # Return an average of recent sold listings to smooth outliers
            avg_price = sum(prices) / len(prices)
            logger.debug(f"Ebay sold average for '{item_title[:30]}': ${avg_price:.2f}")
            return avg_price

    except Exception as e:
        logger.error(f"Failed to scrape eBay for {item_title[:30]}: {e}")

    return 0.0

async def calculate_arbitrage_margins():
    conn = sqlite3.connect("arbitrage_data.db")
    cursor = conn.cursor()

    # Fetch unprocessed listings
    cursor.execute('''
        SELECT id, title, price, hardware_class
        FROM listings
        WHERE processed = FALSE
    ''')
    listings = cursor.fetchall()

    if not listings:
        logger.info("No unprocessed listings found.")
        conn.close()
        return

    logger.info(f"Processing {len(listings)} listings for arbitrage...")

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        for listing in listings:
            list_id, title, local_price, hw_class = listing

            # Determine Shipping
            shipping_cost = SHIPPING_COSTS.get(hw_class, 25.00) # Default to 25 if unclassified

            # Get eBay Sold Price
            ebay_sold_price = await scrape_ebay_sold_price(page, title)

            if ebay_sold_price > 0:
                 # Calculate Margin: (eBay Sold Price) - (Local Price) - (Shipping)
                 # Note: If it's heavy infrastructure, shipping is 0 to calculate raw local margin
                 margin = ebay_sold_price - local_price - shipping_cost
            else:
                 margin = None # Could not determine value

            logger.info(f"ID {list_id}: {title[:30]} | Local: ${local_price} | Sold: ${ebay_sold_price} | Ship: ${shipping_cost} | Margin: ${margin if margin is not None else 0}")

            # Update DB
            cursor.execute('''
                UPDATE listings
                SET ebay_sold_price = ?, margin = ?, shipping_cost = ?, processed = TRUE
                WHERE id = ?
            ''', (ebay_sold_price, margin, shipping_cost, list_id))
            conn.commit()

            # Avoid hammering eBay
            await stealth_delay(3000, 8000)

        await browser.close()
    conn.close()
    logger.info("Arbitrage calculation complete.")

if __name__ == "__main__":
    asyncio.run(calculate_arbitrage_margins())
