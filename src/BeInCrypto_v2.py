import feedparser
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from datetime import datetime, timedelta
import time
import json

# RSS + Playwright approach 

# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create dated filename
filename = f"BeInCrypto_articles_24h_{today_str}.json"

# Full content scraper for BeInCrypto articles
def get_url_content_playwright_beincrypto(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                            (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.google.com"
                }
            )
            page = context.new_page()
            stealth_sync(page)

            page.goto(url, timeout=60000)
            page.wait_for_selector("body", timeout=20000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)

            html = page.content()
            browser.close()

            soup = BeautifulSoup(html, "html.parser")
            container = soup.select_one("div.entry-content")
            paragraphs = container.find_all("p") if container else []
            paragraph_count = len(paragraphs)

            # For now we limit to 10 paragraphs
            return (
                "\n".join(p.get_text(strip=True) for p in paragraphs[:12]) if paragraphs else "No entry-content <p> tags found",
                paragraph_count
            )


    except Exception as e:
        return f"❌ Stealth Playwright error: {e}"

# 📡 RSS fetch + filter by 24h + full scrape
def fetch_beincrypto_last_24h():
    url = "https://beincrypto.com/feed/"
    feed = feedparser.parse(url)
    articles = []

    now = datetime.utcnow()
    cutoff = now - timedelta(days=1)

    for entry in feed.entries:
        published_parsed = entry.get("published_parsed")
        if not published_parsed:
            continue

        published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
        if published_dt < cutoff:
            continue  # Only articles from the last 24 hours

        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        raw_description = entry.get("summary", "") or entry.get("description", "")
        soup = BeautifulSoup(raw_description, "html.parser")
        post = soup.get_text(strip=True)

        print(f"[{published_dt}] Fetching: {title}")
        url_content, paragraph_count = get_url_content_playwright_beincrypto(link)

        articles.append({
            "title": title,
            "post": post,
            "url": link,
            "views": None,
            "reposts": None,
            "url_content": url_content,
            "paragraph_count": paragraph_count,  
            "source": "BeInCrypto",
            "published": published_dt.isoformat()
        })

    return articles

# Run + save
if __name__ == "__main__":
    articles = fetch_beincrypto_last_24h()

    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"Published: {a['published']}")
        print(f"Full content: {a['url_content'][:500]}...") # Limits to 500 characters
        print(f"Paragraphs: {a['paragraph_count']}")
        print(f"{a['url']}")
        print("-" * 60)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")
