# Cointelegraph News Scraper
# Method: RSS + Headless scraping with Playwright
# - RSS feed provides metadata (title, link, publish time)
# - Playwright fetches full HTML content of each article
# - Scraper extracts short summary from <meta> and full content from article body

import feedparser  # Parses RSS feeds
from bs4 import BeautifulSoup  # Parses HTML content
from playwright.sync_api import sync_playwright  # Controls headless Chromium browser
from datetime import datetime, timedelta  # Date filtering
import time  # Convert struct_time to datetime
import json  # Save output as JSON

# Format today's date for filename
today_str = datetime.now().strftime("%m_%d_%Y")
filename = f"Cointelegraph_articles_24h_{today_str}.json"

# Scrape summary + full content from article page using Playwright
def get_cointelegraph_post_and_content(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Visit article URL
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)  # Wait for content to load

            html = page.content()
            browser.close()

            # Parse page HTML
            soup = BeautifulSoup(html, "html.parser")

            # Extract short post from <meta name="description">
            meta_desc = soup.find("meta", {"name": "description"})
            post = meta_desc["content"] if meta_desc and meta_desc.has_attr("content") else ""

            # Extract full content from article body paragraphs
            content_container = soup.select_one("div.post-content.relative")
            paragraphs = content_container.find_all("p") if content_container else []
            paragraph_count = len(paragraphs)
            url_content = "\n".join(p.get_text(strip=True) for p in paragraphs) if paragraphs else "⚠️ No <p> tags found"

            return post, url_content, paragraph_count

    except Exception as e:
        print(f"❌ Error fetching article content from {url} → {e}")
        return "", "", 0

# Fetch from RSS feed and scrape full content for articles in the last 24 hours
def fetch_cointelegraph_last_24h():
    feed_url = "https://cointelegraph.com/rss"
    feed = feedparser.parse(feed_url)
    articles = []

    now = datetime.utcnow()
    cutoff = now - timedelta(days=1)

    for entry in feed.entries:
        published_parsed = entry.get("published_parsed")
        if not published_parsed:
            continue

        # Convert time to datetime object
        published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
        if published_dt < cutoff:
            continue  # Skip old articles

        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()

        print(f"[{published_dt}] Scraping: {title}")
        post, url_content, paragraph_count = get_cointelegraph_post_and_content(url)

        articles.append({
            "title": title,
            "post": post,
            "url": url,
            "views": None,
            "reposts": None,
            "url_content": url_content,
            "paragraph_count": paragraph_count,
            "source": "Cointelegraph",
            "published": published_dt.isoformat()
        })

    return articles, paragraph_count

# Run the scraper
if __name__ == "__main__":
    articles, paragraph_count = fetch_cointelegraph_last_24h()

    # Display in console
    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"Published: {a['published']}")
        print(f"Post: {a['post'][:100]}...")
        print(f"Content: {a['url_content'][:500]}...")
        print(f"Paragraphs: {a['paragraph_count']}")
        print(f"{a['url']}")
        print("-" * 60)

    # Save results to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(articles)} articles to {filename}")
