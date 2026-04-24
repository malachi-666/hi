import asyncio
import json
import re
import random
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import stealth

from src.database import insert_asset
from src.alert_engine import trigger_strike_notification
from src.intelligence import analyze_listing

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "targets.json"

# Desperation & Waste NLP Markers
DISTRESS_PHRASES = [
    "eviction", "divorce", "moving today", "scrap", "take it all",
    "cleaning out the garage", "wife says it has to go", "needs gone asap",
    "must go", "free to a good home", "getting rid of"
]

def calculate_desperation_score(text: str) -> int:
    """Scans for exact high-distress liquidation markers. Returns a score based on hits."""
    text_lower = text.lower()
    score = 0
    for phrase in DISTRESS_PHRASES:
        if phrase in text_lower:
            score += 10
    return score

def extract_liquidity_pressure(description: str) -> str:
    score = calculate_desperation_score(description)
    if score >= 20: return "CRITICAL DISTRESS (Divorce/Eviction)"
    if score >= 10: return "High Distress (Moving/Cleaning)"
    return "Normal"

def clean_price(price_str):
    try:
        clean_str = re.sub(r'[^\d.]', '', price_str)
        return float(clean_str) if clean_str else 0.0
    except ValueError:
        return 0.0

def evaluate_pennies_on_dollar_gate(listed_price, intrinsic_value):
    """
    STRICT ROI GATING:
    The system must automatically discard any listing where the listed_price
    is greater than 15% of the asset's known intrinsic_value.
    """
    if listed_price <= (0.15 * intrinsic_value):
        return True
    return False

async def random_delay():
    await asyncio.sleep(random.uniform(2.1, 4.8))

async def scrape_ksl(context, category, query, max_price, intrinsic_value):
    page = await context.new_page()
    await stealth(page)

    # 30-Mile radius around Bluffdale (Zip 84065) logic would typically be injected here via query params
    # For KSL, usually handled by zip code & miles: &zip=84065&miles=30
    search_url = f"https://classifieds.ksl.com/search/keyword/{query.replace(' ', '%20')}/priceTo/{max_price}/zip/84065/miles/30"

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_selector('section.listing-group', timeout=10000)
        await random_delay()
        soup = BeautifulSoup(await page.content(), 'html.parser')

        listings = soup.find_all('div', class_='listing-item')

        for item in listings:
            title_elem = item.find('h2', class_='title')
            price_elem = item.find('h3', class_='price')
            link_elem = item.find('a', class_='link')

            img_elem = item.find('img')
            image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
            if image_url.startswith("//"): image_url = "https:" + image_url

            desc_elem = item.find('div', class_='description')
            description = desc_elem.text.strip() if desc_elem else ""

            if title_elem and price_elem and link_elem:
                listed_price = clean_price(price_elem.text)

                if evaluate_pennies_on_dollar_gate(listed_price, intrinsic_value):
                    url = "https://classifieds.ksl.com" + link_elem['href']

                    # NLP Forensics
                    pressure = extract_liquidity_pressure(title_elem.text + " " + description)
                    ai_analysis = analyze_listing(title_elem.text, description, category)

                    inserted = insert_asset(
                        platform="KSL", category=category, title=title_elem.text.strip(),
                        listed_price=listed_price, intrinsic_value=intrinsic_value,
                        url=url, image_url=image_url, description=description,
                        liquidity_pressure=pressure, condition_score=ai_analysis['condition_score'],
                        hidden_gem=ai_analysis['hidden_gem'], ai_notes=ai_analysis['ai_notes']
                    )

                    if inserted:
                        asset_data = {
                            "platform": "KSL", "title": title_elem.text.strip(),
                            "listed_price": listed_price, "predicted_profit_margin": intrinsic_value - listed_price - 10,
                            "liquidity_pressure": pressure, "url": url
                        }
                        trigger_strike_notification(asset_data)

    except Exception as e:
        pass
    finally:
        await page.close()

async def scrape_fb(context, category, query, max_price, intrinsic_value):
    page = await context.new_page()
    await stealth(page)

    # 30-Mile radius around Bluffdale (exactRadius=48km)
    search_url = f"https://www.facebook.com/marketplace/saltlakecity/search/?daysSinceDays=1&exactRadius=48&query={query.replace(' ', '%20')}&maxPrice={max_price}"

    try:
        await page.goto(search_url, wait_until="networkidle", timeout=15000)
        await random_delay()

        # Scroll once to trigger lazy load
        await page.keyboard.press("End")
        await random_delay()

        soup = BeautifulSoup(await page.content(), 'html.parser')

        listings = soup.find_all('a', href=lambda href: href and '/marketplace/item/' in href)
        for item in listings:
            price_texts = [span.text for span in item.find_all('span') if '$' in span.text or 'Free' in span.text]
            text_elements = [div.text for div in item.find_all('span') if len(div.text) > 10 and '$' not in div.text]

            if price_texts and text_elements:
                listed_price = clean_price(price_texts[0]) if 'Free' not in price_texts[0] else 0.0

                if evaluate_pennies_on_dollar_gate(listed_price, intrinsic_value):
                    url = "https://www.facebook.com" + item['href'].split('?')[0]
                    img_elem = item.find('img')
                    image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""

                    title = text_elements[0]
                    pressure = extract_liquidity_pressure(title)
                    ai_analysis = analyze_listing(title, "", category)

                    inserted = insert_asset(
                        platform="Facebook", category=category, title=title,
                        listed_price=listed_price, intrinsic_value=intrinsic_value,
                        url=url, image_url=image_url, description="",
                        liquidity_pressure=pressure, condition_score=ai_analysis['condition_score'],
                        hidden_gem=ai_analysis['hidden_gem'], ai_notes=ai_analysis['ai_notes']
                    )

                    if inserted:
                        asset_data = {
                            "platform": "Facebook", "title": title,
                            "listed_price": listed_price, "predicted_profit_margin": intrinsic_value - listed_price - 10,
                            "liquidity_pressure": pressure, "url": url
                        }
                        trigger_strike_notification(asset_data)

    except Exception as e:
        pass
    finally:
        await page.close()

async def execute_scraper():
    if not CONFIG_PATH.exists(): return
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Persistent context localized to Bluffdale, UT
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            geolocation={"longitude": -111.9391, "latitude": 40.4950},
            permissions=["geolocation"]
        )

        tasks = []
        for target in config["targets"]:
            cat = target.get("category", "Uncategorized")
            # Override max_price to enforce the 15% intrinsic value gate during search
            max_p = int(target["intrinsic_value"] * 0.15)
            intrinsic = target["intrinsic_value"]
            for alias in target["search_aliases"]:
                tasks.append(scrape_ksl(context, cat, alias, max_p, intrinsic))
                tasks.append(scrape_fb(context, cat, alias, max_p, intrinsic))

        chunk_size = 3
        for i in range(0, len(tasks), chunk_size):
            await asyncio.gather(*tasks[i:i+chunk_size])
            await random_delay()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(execute_scraper())
