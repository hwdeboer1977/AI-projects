# The Block Article Scraper (Single Article)
# Method: ScraperAPI (proxy service) + BeautifulSoup
# - Requires ScraperAPI key (inserted via .env file)
# - No RSS feed support → article must be scraped manually
# - Article is parsed from <article><p> using simple static HTML parsing
# - Optional debug output saves raw HTML to disk

import requests  # HTTP requests
from bs4 import BeautifulSoup  # Parses HTML
import json  # Save results
import os  # File system operations
from dotenv import load_dotenv  # Load .env credentials
from datetime import datetime, timedelta

# Load ScraperAPI key from .env file
load_dotenv()
SCRAPER_API_KEY = os.getenv("SCRAPER_API")

# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create folder for today (e.g. Output_05_26_2025)
output_dir = f"Output_{today_str}"
os.makedirs(output_dir, exist_ok=True)

# Set filename path inside that folder
filename = os.path.join(output_dir, f"Theblock_articles_24h_{today_str}.json")

# Target article URL
url = "https://www.theblock.co/post/354709/alchemy-acquires-solana-infrastructure-provider-dexterlab-as-it-continues-expansion-beyond-ethereum"

# Scrapes a single article via ScraperAPI
def get_article_scraperapi(url, debug=False):
    try:
        # Set up API request payload
        payload = {
            "api_key": SCRAPER_API_KEY,
            "url": url,
            # "render": "true"  # Uncomment if JS rendering is needed (costly)
        }

        print(f"Fetching via ScraperAPI: {url}")
        r = requests.get("https://api.scraperapi.com", params=payload, timeout=30)
        r.raise_for_status()
        html = r.text

        # Save raw HTML to debug file if enabled
        if debug:
            os.makedirs("debug", exist_ok=True)
            with open("debug/theblock_scraperapi_debug.html", "w", encoding="utf-8") as f:
                f.write(html)

        # Extract <article><p> content
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.select("article p")
        paragraph_count = len(paragraphs)

        article_text = (
            "\n".join(p.get_text(strip=True) for p in paragraphs)
            if paragraphs else "No <p> tags found"
        )

        return {
            "url": url,
            "url_content": article_text,
            "paragraph_count": paragraph_count,
            "source": "The Block"
        }

    except Exception as e:
        return {
            "url": url,
            "url_content": f"ScraperAPI error: {e}",
            "source": "The Block"
        }

# Run as a standalone script
if __name__ == "__main__":
    DEBUG = True  # Set to True to dump HTML for inspection
    article = get_article_scraperapi(url, debug=DEBUG)

    # Print preview to console
    print(f"\n Article Content Preview:\n{article['url_content'][:800]}...\n")
    print(f"{article['url']}\n")
    print(f"Paragraphs: {article['paragraph_count']}")

    # Save result to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)

    print("Article saved to theblock_article_scraperapi.json")
