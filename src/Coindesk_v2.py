import feedparser # Parses RSS feeds and handles common edge cases like CDATA, namespaces
import requests # Used to fetch the raw RSS XML for ET parsing
import xml.etree.ElementTree as ET # Low-level XML parsing to extract <description>
import re
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time



# Use xml.etree.ElementTree (ET) – to parse the RSS feed
# playwright – to extract full content (url_content) by visiting each article link
# BeautifulSoup – to parse the HTML returned by playwright and extract the first few <p> paragraphs
# BeautifulSoup Ensures all content (e.g., full article text) is rendered


# feedparser: title + url
# ElementTree from raw XML: Guarantees extraction from <description> to fill POST
# feedparser.content[0]['value']: HTML-parsed full article body to fill URL_CONTENT

# feedparser for RSS: high level, tolerant
# Previous Script (ET + playwright): low level, more control

# feedparser extracts post from <description>/<summary>
# Previous Script (ET + playwright): Same, but sometimes CDATA may be missed

# feedparser does not support JavaScript-rendered pages
# Previous Script (ET + playwright): supports JavaScript-rendered pages via playwright

# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create dated filename
filename = f"Coindesk_articles_24h_{today_str}.json"

def fetch_coindesk_last_24h():
    rss_url = "https://feeds.feedburner.com/CoinDesk"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []

    # Time filter setup
    now = datetime.utcnow()
    cutoff = now - timedelta(days=1)

    # STEP 1: Raw XML parsing for <description>
    xml_raw = requests.get(rss_url, headers=headers).content
    xml_root = ET.fromstring(xml_raw)
    raw_items = xml_root.findall(".//item")

    # STEP 2: Parse feed with feedparser for easy access
    parsed_feed = feedparser.parse(xml_raw)

    # STEP 3: Filter + extract data
    for entry in parsed_feed.entries:
        published_parsed = entry.get("published_parsed")
        if not published_parsed:
            continue

        published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
        if published_dt < cutoff:
            continue  # Skip old articles

        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        # Match raw <item> to get <description>
        raw_post = ""
        for item in raw_items:
            item_title = item.findtext("title", default="").strip()
            if item_title == title:
                raw_description = item.findtext("description", default="").strip()
                raw_post = BeautifulSoup(raw_description, "html.parser").get_text(strip=True)
                break

        # Extract full content from <content:encoded>
        url_content = ""
        content_list = entry.get("content", [])
        if content_list and isinstance(content_list, list) and "value" in content_list[0]:
            soup = BeautifulSoup(content_list[0]["value"], "html.parser")
            paragraphs = soup.find_all("p")
            paragraph_count = len(paragraphs)
            url_content = "\n".join(p.get_text(strip=True) for p in paragraphs[:12])

        results.append({
            "title": title,
            "post": raw_post,
            "url": link,
            "views": None,
            "reposts": None,
            "url_content": url_content,
            "paragraph_count": paragraph_count,
            "source": "CoinDesk",
            "published": published_dt.isoformat()
        })

    return results

# Main runner
if __name__ == "__main__":
    articles = fetch_coindesk_last_24h()

    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"Published: {a['published']}")
        print(f"Summary: {a['post'][:100]}...")
        print(f"Full Content: {a['url_content'][:500]}...")
        print(f"Paragraphs: {a['paragraph_count']}")
        print(f"{a['url']}")
        print("-" * 60)


    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")