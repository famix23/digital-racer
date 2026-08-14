import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# --- CONFIGURATION ---
CATALOG_URL = "https://zeusx.com/game/pubg-mobile/22/accounts?page=1"
BASE_DOMAIN = "https://zeusx.com"
PROFIT_MARKUP_PERCENT = 20  # Adds 20% to the original price
MINIMUM_MARKUP_USD = 10     # Ensures a minimum profit per account

# Mimic a real browser to bypass basic bot protection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://zeusx.com/"
}

def sanitize_text(text: str) -> str:
    """Removes third-party platform mentions to white-label the description."""
    if not text:
        return "Instant delivery verified PUBG Mobile account."
    
    replacements = {
        r"(?i)zeusx": "Digital Racer",
        r"(?i)trusted seller": "Verified Inventory",
        r"(?i)pm me": "Contact Support",
        r"(?i)whatsapp": "Our Official Support",
    }
    cleaned = text
    for pattern, replacement in replacements.items():
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned.strip()

def calculate_price(raw_price: float) -> str:
    """Applies your profit markup formula."""
    markup = max(raw_price * (PROFIT_MARKUP_PERCENT / 100), MINIMUM_MARKUP_USD)
    final_price = raw_price + markup
    return f"{final_price:.2f}"

def fetch_product_details(product_url):
    """Visits the specific product page to get full descriptions and original images."""
    print(f"Scraping product page: {product_url}")
    try:
        # Pause slightly so we don't trigger anti-bot limits
        time.sleep(1.5) 
        
        response = requests.get(product_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. Get the Full Title
        title_elem = soup.select_one("h1, .product-title")
        raw_title = title_elem.get_text(strip=True) if title_elem else "PUBG Mobile Premium Account"
        
        # 2. Get the Price
        price_elem = soup.select_one(".price, span:contains('$')")
        raw_price_str = re.sub(r"[^\d.]", "", price_elem.get_text(strip=True)) if price_elem else "0"
        try:
            raw_price = float(raw_price_str)
        except ValueError:
            raw_price = 0.0

        # 3. Get the Original Uploaded Image
        # Looks for the main gallery image wrapper
        image_url = ""
        img_elem = soup.select_one(".gallery img, .product-image img, img[alt*='PUBG']")
        if img_elem:
            image_url = img_elem.get("src") or img_elem.get("data-src") or ""
        
        # Fallback to a placeholder if the seller didn't use an image
        if not image_url or image_url.startswith("data:"):
            image_url = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1000"

        # 4. Get the Full Description
        desc_elem = soup.select_one(".description, .product-desc, article")
        raw_desc = desc_elem.get_text(separator="\n", strip=True) if desc_elem else raw_title

        return {
            "title": raw_title,
            "price": calculate_price(raw_price),
            "image": image_url,
            "description": sanitize_text(raw_desc)
        }
    except Exception as e:
        print(f"Failed to load details for {product_url}: {e}")
        return None

def fetch_and_parse_inventory():
    """Step 1: Scrape the main catalog feed to find the links to the individual accounts."""
    response = requests.get(CATALOG_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    catalog_items = []
    
    # Find all product cards that contain a link to a specific account
    listing_cards = soup.select("a[href*='/game/pubg-mobile/']")
    
    # We use a set to avoid processing the same link twice if it appears multiple times on the page
    unique_links = list(set([card.get("href") for card in listing_cards if card.get("href")]))
    
    print(f"Found {len(unique_links)} products on the catalog page. Extracting data...")

    # Step 2: Visit the top 15 listings to extract full data (capping at 15 to keep the script fast)
    for link in unique_links[:15]:
        full_product_url = urljoin(BASE_DOMAIN, link)
        product_data = fetch_product_details(full_product_url)
        
        if product_data and float(product_data["price"]) > 0:
            catalog_items.append(product_data)

    return catalog_items

def main():
    try:
        items = fetch_and_parse_inventory()
        if not items:
            print("No items parsed. Retaining existing inventory.")
            return

        payload = {"catalog": items}

        # Write directly to your CMS JSON file
        with open("inventory.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

        print(f"Successfully synced {len(items)} detailed, white-labeled products.")
    except Exception as e:
        print(f"Sync error encountered: {e}")

if __name__ == "__main__":
    main()
