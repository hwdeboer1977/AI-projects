import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import undetected_chromedriver as uc
import time
import json
import os

# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create dated filename
filename = f"Defiant_articles_24h_{today_str}.json"

def get_url_content_udc(url, debug=False):
    try:
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=en-US,en;q=0.9")

        driver = uc.Chrome(options=options)
        print(f"Visiting: {url}")
        driver.get(url)
        time.sleep(5)

        for _ in range(3):
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight / 3)")
            time.sleep(1)

        html = driver.page_source
        driver.quit()

        if debug:
            os.makedirs("debug", exist_ok=True)
            with open("debug/latest_defiant_article.html", "w", encoding="utf-8") as f:
                f.write(html)

        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.select("article p")
        paragraph_count = len(paragraphs)


        url_content = "\n".join(p.get_text(strip=True) for p in paragraphs) if paragraphs else "⚠️ No post-content <p> tags found"
        return url_content, paragraph_count

    except Exception as e:
        return f"❌ UDC error: {e}"

def fetch_defiant_articles_24h(debug=False):
    feed_url = "https://thedefiant.io/feed/"
    feed = feedparser.parse(feed_url)
    now = datetime.utcnow()
    cutoff = now - timedelta(days=1)

    articles = []

    for entry in feed.entries:
        
        published_parsed = entry.get("published_parsed")
        if not published_parsed:
            continue

        published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
        if published_dt < cutoff:
            continue

        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        raw_description = entry.get("summary", "") or entry.get("description", "")
        soup = BeautifulSoup(raw_description, "html.parser")
        post = soup.get_text(strip=True)

        print(f"[{published_dt}] Fetching: {title}")
        url_content, paragraph_count = get_url_content_udc(link, debug=debug)

        articles.append({
            "title": title,
            "post": post,
            "url": link,
            "url_content": url_content,
            "paragraph_count": paragraph_count,
            "source": "The Defiant",
            "published": published_dt.isoformat()
        })

    return articles

if __name__ == "__main__":
    DEBUG = False  # Set True to dump HTML of last article
    articles = fetch_defiant_articles_24h(debug=DEBUG)

    for i, a in enumerate(articles, 1):
        print(f"\n[{i}] {a['title']}")
        print(f" {a['published']}")
        print(f" Preview:\n{a['url_content'][:400]}...\n")
        print(f"Paragraphs: {a['paragraph_count']}")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")