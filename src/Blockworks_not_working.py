from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json

def extract_article_data(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        # Timestamp
        published_dt = None
        time_tag = soup.find("time", {"datetime": True})
        if time_tag:
            try:
                published_dt = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
            except:
                pass

        # Meta description
        meta_desc = soup.find("meta", {"name": "description"})
        post = meta_desc["content"] if meta_desc and meta_desc.has_attr("content") else ""

        # Full content (first few <p> tags)
        content_container = soup.select_one("article")
        paragraphs = content_container.find_all("p") if content_container else []
        url_content = "\n".join(p.get_text(strip=True) for p in paragraphs[:8]) if paragraphs else "⚠️ No <p> tags found"

        return published_dt, post, url_content

    except Exception as e:
        print(f"❌ Error fetching article content from {url} → {e}")
        return None, "", ""

def scrape_news_site(name, url, base_url, selector, limit=10):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select(selector)

    seen = set()
    results = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    for a in articles:
        title = a.get_text(strip=True)
        href = a.get("href")
        if not title or not href or href in seen or not href.startswith("/"):
            continue

        full_url = base_url + href
        seen.add(href)

        published_dt, post, url_content = extract_article_data(full_url)
        if not published_dt or published_dt < cutoff:
            continue

        results.append({
            "source": name,
            "title": title,
            "link": full_url,
            "published": published_dt.isoformat(),
            "post": post,
            "url_content": url_content,
            "views": None,
            "reposts": None
        })

        if len(results) >= limit:
            break

    return results

if __name__ == "__main__":
    sources = [
        {
            "name": "Blockworks",
            "url": "https://blockworks.co/news",
            "base_url": "https://blockworks.co",
            "selector": "a[href^='/news/']"
        }
    ]

    all_articles = []
    for site in sources:
        print(f"Fetching from {site['name']}...")
        try:
            articles = scrape_news_site(site["name"], site["url"], site["base_url"], site["selector"], limit=10)
            all_articles.extend(articles)
        except Exception as e:
            print(f"Failed to scrape {site['name']}: {e}")

    for i, a in enumerate(all_articles, 1):
        print(f"[{i}] [{a['source']}] {a['title']}")
        print(f"🕒 Published: {a['published']}")
        print(f"📰 Post: {a['post'][:100]}...")
        print(f"📄 Content: {a['url_content'][:300]}...")
        print(f"🔗 {a['link']}")
        print("-" * 60)

    with open("blockworks_24h_articles.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(all_articles)} articles to blockworks_24h_articles.json")
