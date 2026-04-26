import asyncio
import random
import sqlite3
import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page
from loguru import logger
import re

DB_NAME = "arbitrage_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
    return conn

def insert_listing(conn: sqlite3.Connection, listing: Dict[str, Any]):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO listings (source, title, price, url, location, scraped_at, hardware_class)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            listing['source'],
            listing['title'],
            listing['price'],
            listing['url'],
            listing['location'],
            datetime.datetime.now().isoformat(),
            listing.get('hardware_class', 'Unknown')
        ))
        conn.commit()
        logger.info(f"Inserted: {listing['title']} (${listing['price']}) from {listing['source']}")
    except sqlite3.IntegrityError:
        logger.debug(f"Listing already exists: {listing['url']}")

async def stealth_delay(min_ms: int = 1000, max_ms: int = 3000):
    delay = random.uniform(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)

async def scrape_ksl(page: Page, search_term: str = "server") -> List[Dict[str, Any]]:
    listings = []
    logger.info(f"Scraping KSL for '{search_term}'...")
    url = f"https://classifieds.ksl.com/search?keyword={search_term}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await stealth_delay(2000, 4000)

        # This is a generic selector; will likely need refinement based on actual KSL DOM
        items = await page.query_selector_all("div.listing-item")
        for item in items:
            try:
                title_elem = await item.query_selector("h2.title a")
                if not title_elem:
                    continue
                title = await title_elem.inner_text()
                link = await title_elem.get_attribute("href")
                if not link.startswith("http"):
                    link = "https://classifieds.ksl.com" + link

                price_elem = await item.query_selector("h3.price")
                price_str = await price_elem.inner_text() if price_elem else "0"
                price_match = re.search(r'[\d,]+(\.\d{2})?', price_str)
                price = float(price_match.group(0).replace(',', '')) if price_match else 0.0

                location_elem = await item.query_selector("span.address")
                location = await location_elem.inner_text() if location_elem else "Unknown"

                listings.append({
                    "source": "KSL Classifieds",
                    "title": title.strip(),
                    "price": price,
                    "url": link,
                    "location": location.strip(),
                    "hardware_class": classify_hardware(title)
                })
            except Exception as e:
                logger.error(f"Error parsing KSL item: {e}")
    except Exception as e:
        logger.error(f"Failed to scrape KSL: {e}")
    return listings

async def scrape_craigslist(page: Page, search_term: str = "server") -> List[Dict[str, Any]]:
    listings = []
    logger.info(f"Scraping Craigslist for '{search_term}'...")
    url = f"https://saltlakecity.craigslist.org/search/sss?query={search_term}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await stealth_delay(2000, 4000)

        items = await page.query_selector_all("li.cl-search-result")
        for item in items:
            try:
                title_elem = await item.query_selector("a.cl-app-title")
                if not title_elem:
                    continue
                title = await title_elem.inner_text()
                link = await title_elem.get_attribute("href")

                price_elem = await item.query_selector("span.priceinfo")
                price_str = await price_elem.inner_text() if price_elem else "0"
                price_match = re.search(r'[\d,]+(\.\d{2})?', price_str)
                price = float(price_match.group(0).replace(',', '')) if price_match else 0.0

                location_elem = await item.query_selector("div.meta")
                location = await location_elem.inner_text() if location_elem else "Salt Lake City Area"

                listings.append({
                    "source": "Craigslist",
                    "title": title.strip(),
                    "price": price,
                    "url": link,
                    "location": location.strip(),
                    "hardware_class": classify_hardware(title)
                })
            except Exception as e:
                logger.error(f"Error parsing Craigslist item: {e}")
    except Exception as e:
         logger.error(f"Failed to scrape Craigslist: {e}")
    return listings

def classify_hardware(title: str) -> str:
    title_lower = title.lower()
    if "server" in title_lower or "rack" in title_lower or "switch" in title_lower or "cisco" in title_lower or "dell poweredge" in title_lower:
        return "Heavy Infrastructure"
    elif "laptop" in title_lower or "macbook" in title_lower or "thinkpad" in title_lower:
        return "Laptop"
    elif "ram" in title_lower or "ddr" in title_lower or "cpu" in title_lower or "gpu" in title_lower or "ssd" in title_lower:
        return "Components"
    elif "monitor" in title_lower or "display" in title_lower or "crt" in title_lower:
         return "Heavy Infrastructure"
    else:
        return "General Electronics"

async def main():
    conn = init_db()

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        search_terms = ["server", "laptop", "cisco", "ddr4"]

        all_listings = []
        for term in search_terms:
            ksl_res = await scrape_ksl(page, term)
            cl_res = await scrape_craigslist(page, term)
            all_listings.extend(ksl_res)
            all_listings.extend(cl_res)
            await stealth_delay(5000, 10000)

        logger.info(f"Total scraped items this run: {len(all_listings)}")
        for listing in all_listings:
            insert_listing(conn, listing)

        await browser.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
