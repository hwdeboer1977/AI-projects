from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from dateutil import parser
import json
import time


# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create dated filename
filename = f"Bankless_articles_24h_{today_str}.json"

def scrape_bankless_articles(limit=5):
    results = []
    seen = set()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)


    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.bankless.com/published", timeout=60000)
        page.wait_for_timeout(3000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select("a[href^='/']")

        for link in links:
            href = link.get("href")
            full_url = "https://www.bankless.com" + href
            title = link.get_text(strip=True)

            if not href or not title or href in seen or not href.startswith("/"):
                continue
            seen.add(href)

            print(f"📰 Scraping: {title}")
            article_page = context.new_page()
            article_page.goto(full_url, timeout=60000)
            article_page.wait_for_timeout(3000)

            article_html = article_page.content()
            article_soup = BeautifulSoup(article_html, "html.parser")

            # Timestamp
            published_dt = None
            meta_time = article_soup.find("meta", {"property": "article:published_time"})
            if meta_time and meta_time.get("content"):
                try:
                    published_dt = parser.parse(meta_time["content"]).astimezone(timezone.utc)
                except:
                    pass
            else:
                time_tag = article_soup.find("time")
                if time_tag:
                    try:
                        published_dt = parser.parse(time_tag.get_text(strip=True)).astimezone(timezone.utc)
                    except:
                        pass

            if not published_dt or published_dt < cutoff:
                article_page.close()
                continue

            # Summary
            meta_desc = article_soup.find("meta", {"name": "description"})
            post = meta_desc.get("content", "").strip() if meta_desc else ""
            if not post:
                first_para = article_soup.select_one("article p")
                post = first_para.get_text(strip=True) if first_para else ""

            # Full content
            prose = article_soup.select_one("article") or article_soup.select_one("div.prose")
            paragraphs = prose.find_all("p") if prose else []
            paragraph_count = len(paragraphs)
            url_content = "\n".join(p.get_text(strip=True) for p in paragraphs[:12]) or "⚠️ No content found"

            article_page.close()

            results.append({
                "title": title,
                "post": post,
                "url": full_url,
                "views": None,
                "reposts": None,
                "url_content": url_content,
                "paragraph_count": paragraph_count,  
                "source": "Bankless",
                "published": published_dt.isoformat()
            })

            if len(results) >= limit:
                break

        browser.close()
    return results

# Run & Save
if __name__ == "__main__":
    articles = scrape_bankless_articles(limit=10)

    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"Published: {a['published']}")
        print(f"Summary: {a['post'][:100]}...")
        print(f"Content: {a['url_content'][:500]}...")
        print(f"Paragraphs: {a['paragraph_count']}")
        print(f"{a['url']}")
        print("-" * 60)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")