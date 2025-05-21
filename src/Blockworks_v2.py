import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import time
import json
import os

BASE_URL = "https://blockworks.co"
NEWS_URL = "https://blockworks.co/news"
CUTOFF_TIME = datetime.now(timezone.utc) - timedelta(days=1)  # fixed for offset-aware comparison

# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create dated filename
filename = f"Blockworks_articles_24h_{today_str}.json"

def get_article_data(url, debug=False):
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
        html = driver.page_source
        driver.quit()

        if debug:
            os.makedirs("debug", exist_ok=True)
            with open("debug/blockworks_article.html", "w", encoding="utf-8") as f:
                f.write(html)

        soup = BeautifulSoup(html, "html.parser")

        # ⏱ Extract publish time (ISO format)
        time_tag = soup.find("time")
        published = time_tag.get("datetime") if time_tag else None
        published_dt = None
        if published:
            try:
                published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except:
                published_dt = None

        # Skip if older than 24h
        if not published_dt or published_dt < CUTOFF_TIME:
            print(f"⏱ Skipped: older than 24h or no time found → {published_dt}")
            return None

        meta_desc = soup.find("meta", {"name": "description"})
        post = meta_desc["content"].strip() if meta_desc and meta_desc.has_attr("content") else ""

        paragraphs = soup.select("article p")
        paragraph_count = len(paragraphs)
        url_content = "\n".join(p.get_text(strip=True) for p in paragraphs) if paragraphs else "⚠️ No <p> tags found"

        return {
            "url": url,
            "source": "Blockworks",
            "published": published_dt.isoformat(),
            "post": post,
            "url_content": url_content,
            "paragraph_count": paragraph_count
        }

    except Exception as e:
        return {
            "url": url,
            "source": "Blockworks",
            "post": "",
            "url_content": f"❌ UDC error: {e}"
        }

def get_recent_blockworks_urls():
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=en-US,en;q=0.9")

    driver = uc.Chrome(options=options)
    print(f"Loading news page: {NEWS_URL}")
    driver.get(NEWS_URL)
    time.sleep(5)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href^='/news/']")
    seen = set()
    article_urls = []

    for link in links:
        href = link.get("href")
        if href and href not in seen and href.startswith("/news/"):
            seen.add(href)
            full_url = BASE_URL + href
            article_urls.append(full_url)

    print(f"Found {len(article_urls)} unique article links")
    return article_urls

# Run the full job
if __name__ == "__main__":
    DEBUG = False
    urls = get_recent_blockworks_urls()
    articles = []

    for url in urls:
        article = get_article_data(url, debug=DEBUG)
        
        if article is None:
            print("Stopping — article is older than 24h.")
            break  # Stop visiting further URLs

        articles.append(article)
        time.sleep(1)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")