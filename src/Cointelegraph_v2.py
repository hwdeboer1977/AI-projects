import feedparser
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import time
import json

# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create dated filename
filename = f"Cointelegraph_articles_24h_{today_str}.json"

# Scrape short summary and full content via Playwright
def get_cointelegraph_post_and_content(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            html = page.content()
            browser.close()

            soup = BeautifulSoup(html, "html.parser")

            # Get short post from <meta name="description">
            meta_desc = soup.find("meta", {"name": "description"})
            post = meta_desc["content"] if meta_desc and meta_desc.has_attr("content") else ""

            # Get full content from article paragraphs
            content_container = soup.select_one("div.post-content.relative")
            paragraphs = content_container.find_all("p") if content_container else []
            paragraph_count = len(paragraphs)
            url_content = "\n".join(p.get_text(strip=True) for p in paragraphs[:12]) if paragraphs else "⚠️ No <p> tags found"

            return post, url_content, paragraph_count

    except Exception as e:
        print(f"❌ Error fetching article content from {url} → {e}")
        return "", ""

# Fetch articles from RSS and filter last 24h
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

        published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
        if published_dt < cutoff:
            continue

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

# Run + Save
if __name__ == "__main__":
    articles, paragraph_count = fetch_cointelegraph_last_24h()

    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"Published: {a['published']}")
        print(f"Post: {a['post'][:100]}...")
        print(f"Content: {a['url_content'][:500]}...")
        print(f"Paragraphs: {a['paragraph_count']}")
        print(f" {a['url']}")
        print("-" * 60)


    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")