import requests
import os
import json
import time
import re
import urllib.parse
from dotenv import load_dotenv
from datetime import datetime

# ——————————————————————————————
# ✅ 1. Config & Setup
load_dotenv()
API_KEY = os.getenv("TWITTER_IO_API")
if not API_KEY:
    raise ValueError("Missing TWITTER_IO_API in .env")

HEADERS = {"x-api-key": API_KEY}

# ——————————————————————————————
# 📆 2. Date settings
today_str = datetime.utcnow().strftime("%m_%d_%Y")
#date_str = "06_12_2025"  # or today_str
date_str = today_str

INPUT_PATH = f"Output_{date_str}/summary_filtered_{date_str}.json"
OUTPUT_PATH = f"Output_{date_str}/summary_with_twitter_{date_str}.json"

def clean(text):
    """Remove non-alphanumeric characters (except space/hyphen)."""
    return re.sub(r"[^\w\s\-]", "", text).strip()

def check_twitter_engagement():
    if not os.path.exists(INPUT_PATH):
        print(f"❌ File not found: {INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    total = len(articles)
    save_interval = 5

    for idx, article in enumerate(articles, 1):
        title = article.get("title", "").strip()
        url = article.get("url", "")
        keywords = article.get("keywords", [])[:2]

        if not title:
            article["twitter_engagement"] = {}
            continue

        # Build search query
        qt = f"\"{clean(title)}\""
        kq = " OR ".join(clean(k) for k in keywords if k)
        uq = urllib.parse.quote(url.split("?")[0])
        query_parts = [qt] + ([kq] if kq else []) + [uq]
        query = " OR ".join(query_parts)

        # Call twitterapi.io advanced search
        resp = requests.get(
            "https://api.twitterapi.io/twitter/tweet/advanced_search",
            headers=HEADERS,
            params={
                "query": query,
                "queryType": "Latest"
            }
        )

        if resp.status_code == 429:
            print(f"🔁 Rate limit hit at article {idx}/{total}. Sleeping 15 minutes...")
            time.sleep(15 * 60)
            continue

        if resp.status_code != 200:
            print(f"❌ Error {resp.status_code} for idx {idx}: {title[:50]}… Skipping.")
            article["twitter_engagement"] = {}
            continue

        # Aggregate engagement from tweets
        tweets = resp.json().get("tweets", [])
        metrics = {"likes": 0, "retweets": 0, "replies": 0, "quotes": 0}
        for t in tweets:
            metrics["likes"] += t.get("likeCount", 0)
            metrics["retweets"] += t.get("retweetCount", 0)
            metrics["replies"] += t.get("replyCount", 0)
            metrics["quotes"] += t.get("quoteCount", 0)

        article["twitter_engagement"] = metrics
        print(f"[{idx}/{total}] {title[:60]} → {metrics}")

        # Periodic save
        if idx % save_interval == 0:
            with open(OUTPUT_PATH, "w", encoding="utf-8") as fw:
                json.dump(articles, fw, indent=2)
            print(f"💾 Partial save at article {idx}/{total}")

        time.sleep(1.2)

    # Final save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fw:
        json.dump(articles, fw, indent=2)
    print(f"✅ Final results saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    check_twitter_engagement()
