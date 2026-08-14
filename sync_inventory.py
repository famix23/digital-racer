import json
import re
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TARGET_URL = "https://zeusx.com/game/pubg-mobile/22/accounts?page=1"
PROFIT_MARKUP_PERCENT = 20  # Adds 20% to the original price
MINIMUM_MARKUP_USD = 10     # Ensures a minimum profit per account
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def sanitize_text(text: str) -> str:
    """Removes third-party platform mentions and cleans up the description."""
    if not text:
        return "Instant delivery verified PUBG Mobile account."
    
    # Remove mentions of ZeusX or specific seller terms
    replacements = {
        r"(?i)zeusx": "Digital Racer",
        r"(?i)trusted seller": "verified inventory",
        r"(?i)pm me": "contact support",
        r"(?i)whatsapp": "our official support",
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

def fetch_and_parse_inventory():
    response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    catalog_items = []

    # Locate product listing containers
    listing_cards = soup.select("div[class*='product'], div[class*='card'], a[href*='/game/pubg-mobile/']")

    for card in listing_cards[:30]:  # Limit to top 30 active listings
        title_elem = card.select_one("h2, h3, [class*='title']")
        price_elem = card.select_one("[class*='price'], span:contains('$')")
        img_elem = card.select_one("img")

        if not (title_elem and price_elem):
            continue

        raw_title = title_elem.get_text(strip=True)
        raw_price_str = re.sub(r"[^\d.]", "", price_elem.get_text(strip=True))
        
        if not raw_price_str:
            continue
            
        try:
            raw_price = float(raw_price_str)
        except ValueError:
            continue

        # Extract direct image source
        image_url = ""
        if img_elem:
            image_url = img_elem.get("src") or img_elem.get("data-src") or ""

        # Default fallback image if missing
        if not image_url or image_url.startswith("data:"):
            image_url = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1000"

        # Build white-labeled item
        item = {
            "title": raw_title,
            "price": calculate_price(raw_price),
            "image": image_url,
            "description": sanitize_text(raw_title)
        }
        catalog_items.append(item)

    return catalog_items

def main():
    try:
        items = fetch_and_parse_inventory()
        if not items:
            print("No items parsed or structure changed. Retaining existing inventory.")
            return

        payload = {"catalog": items}

        with open("inventory.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

        print(f"Successfully synced {len(items)} white-labeled products.")
    except Exception as e:
        print(f"Sync error encountered: {e}")

if __name__ == "__main__":
    main()
