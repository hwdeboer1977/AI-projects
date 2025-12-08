# CoinDesk News Scraper
# Method: RSS-based parsing with hybrid techniques
# - Uses requests + xml.etree.ElementTree for raw <description> fields
# - Uses feedparser for easy access to metadata like title, link, and content:encoded
# - Does not use browser scraping — 100% XML/RSS-based

import feedparser # Parses RSS feeds and handles common edge cases like CDATA, namespaces
import requests # Fetches raw XML content from the feed URL
import xml.etree.ElementTree as ET # Parses low-level <item> and <description> elements
import re
from bs4 import BeautifulSoup # Cleans HTML inside <description> and <content:encoded>
import json
from datetime import datetime, timedelta
import time
import os
import html


# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create folder for today (e.g. Output_05_26_2025)
output_dir = f"Output_{today_str}"
os.makedirs(output_dir, exist_ok=True)

# Set filename path inside that folder
filename = os.path.join(output_dir, f"Coindesk_articles_24h_{today_str}.json")



# Main function to fetch and filter CoinDesk articles from the past 24 hours
def fetch_coindesk_last_24h():
    rss_url = "https://feeds.feedburner.com/CoinDesk"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []

     # Setup: current UTC time and 24h cutoff
    now = datetime.utcnow()
    cutoff = now - timedelta(days=1)

    # STEP 1: Raw XML parsing using ElementTree (for grabbing <description>)
    xml_raw = requests.get(rss_url, headers=headers).content
    xml_root = ET.fromstring(xml_raw)
    raw_items = xml_root.findall(".//item")

     # STEP 2: Parse feed using feedparser for easy metadata access
    parsed_feed = feedparser.parse(xml_raw)

    # STEP 3: Process entries and filter by publish time
    for entry in parsed_feed.entries:
        published_parsed = entry.get("published_parsed")
        if not published_parsed:
            continue # Skip if no timestamp

        published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
        if published_dt < cutoff:
            continue  # Skip articles older than 24h

        #title = entry.get("title", "").strip()
        title = html.unescape(entry.get("title", "").strip())

        link = entry.get("link", "").strip()

         # Match against raw XML <item> to extract <description> text
        raw_post = ""
        for item in raw_items:
            item_title = item.findtext("title", default="").strip()
            if item_title == title:
                raw_description = item.findtext("description", default="").strip()
                raw_post = BeautifulSoup(raw_description, "html.parser").get_text(strip=True)
                break

         # Extract full article body from <content:encoded> field
        url_content = ""
        paragraph_count = 0  # Default if no content found
        content_list = entry.get("content", [])
        if content_list and isinstance(content_list, list) and "value" in content_list[0]:
            soup = BeautifulSoup(content_list[0]["value"], "html.parser")
            paragraphs = soup.find_all("p")
            paragraph_count = len(paragraphs)
            url_content = "\n".join(p.get_text(strip=True) for p in paragraphs) # No Limit on paragraphs

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

     # Display in console
    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"Published: {a['published']}")
        print(f"Summary: {a['post'][:100]}...")
        print(f"Full Content: {a['url_content'][:500]}...")
        print(f"Paragraphs: {a['paragraph_count']}")
        print(f"{a['url']}")
        print("-" * 60)

    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")