import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv

# This only works with ScraperAPI account (but I only have a free account)
# Replace with ScraperAPI key
load_dotenv()
SCRAPER_API_KEY = os.getenv("SCRAPER_API")


# Target article
url = "https://www.theblock.co/post/354709/alchemy-acquires-solana-infrastructure-provider-dexterlab-as-it-continues-expansion-beyond-ethereum"

def get_article_scraperapi(url, debug=False):
    try:
        payload = {
            "api_key": SCRAPER_API_KEY,
            "url": url,
            #"render": "true"  # optional — enables JS rendering
        }

        print(f"🌐 Fetching via ScraperAPI: {url}")
        r = requests.get("https://api.scraperapi.com", params=payload, timeout=30)
        r.raise_for_status()
        html = r.text

        if debug:
            os.makedirs("debug", exist_ok=True)
            with open("debug/theblock_scraperapi_debug.html", "w", encoding="utf-8") as f:
                f.write(html)

        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.select("article p")

        article_text = "\n".join(p.get_text(strip=True) for p in paragraphs) if paragraphs else "⚠️ No <p> tags found"
        return {
            "url": url,
            "url_content": article_text,
            "source": "The Block"
        }

    except Exception as e:
        return {
            "url": url,
            "url_content": f"❌ ScraperAPI error: {e}",
            "source": "The Block"
        }

# ✅ Run
if __name__ == "__main__":
    DEBUG = True
    article = get_article_scraperapi(url, debug=DEBUG)

    print(f"\n📄 Article Content Preview:\n{article['url_content'][:800]}...\n")
    print(f"🔗 {article['url']}\n")

    with open("theblock_article_scraperapi.json", "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)

    print("✅ Article saved to theblock_article_scraperapi.json")
