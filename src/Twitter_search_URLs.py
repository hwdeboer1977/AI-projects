import requests
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load Twitter bearer token
load_dotenv()
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
if not BEARER_TOKEN:
    raise ValueError("Missing TWITTER_BEARER_TOKEN in .env")

# Twitter search endpoint
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

# Setup input file
INPUT_FILE = Path("Cointelegraph_articles_24h_05_21_2025.json")  # Update if needed
OUTPUT_FILE = f"enriched_{INPUT_FILE.name}"



HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

def search_tweets_by_url(url):
    """Searches tweets containing the specified URL."""
    params = {
        "query": f'url:"{url}"',
        "max_results": 50,
        "tweet.fields": "created_at,public_metrics"
    }
    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json().get("data", [])
        return {
            "mention_count": len(data),
            "related_tweets": data
        }
    except Exception as e:
        return {
            "mention_count": 0,
            "related_tweets": [],
            "error": str(e)
        }

def main():
    if not INPUT_FILE.exists():
        print(f"❌ File not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    enriched = []
    for i, entry in enumerate(entries, 1):
        url = entry.get("url")
        if not url:
            continue

        print(f"[{i}/{len(entries)}] Searching mentions for: {url}")
        mention_data = search_tweets_by_url(url)
        entry.update(mention_data)

        enriched.append(entry)
        time.sleep(1)  # Respect Twitter rate limits (30 requests/min)

    # Save output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(enriched)} enriched entries to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
