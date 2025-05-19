import feedparser
from bs4 import BeautifulSoup
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# SOMEHOW NOT ABLE TO GET THE URL_CONTENT!!


def get_url_content_playwright_stealth(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                            (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US"
            )
            page = context.new_page()
            stealth_sync(page)

            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)  # Let JS fully load

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Find the container by checking for at least one <p> inside
            candidate = None
            for div in soup.find_all("div", class_=lambda x: x and "prose" in x):
                if div.find("p"):
                    candidate = div
                    break

            if not candidate:
                return "⚠️ No container with <p> tags found"

            paragraphs = candidate.find_all("p")
            return "\n".join(p.get_text(strip=True) for p in paragraphs[:8]) if paragraphs else "⚠️ No paragraphs found"

    except Exception as e:
        return f"❌ Stealth Playwright error: {e}"



def fetch_defiant_rss(limit=5):
    url = "https://thedefiant.io/feed/"
    feed = feedparser.parse(url)
    results = []

    for entry in feed.entries[:limit]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        raw_description = entry.get("summary", "") or entry.get("description", "") or ""
        soup = BeautifulSoup(raw_description, "html.parser")
        post = soup.get_text(strip=True)

        url_content = get_url_content_playwright_stealth(link)

        results.append({
            "title": title,
            "post": post,
            "url": link,
            "views": None,
            "reposts": None,
            "url_content": url_content,
            "source": "The Defiant"
        })

    return results

if __name__ == "__main__":
    articles = fetch_defiant_rss(limit=5)

    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"📰 POST: {a['post'][:100]}...")
        #print(f"📄 CONTENT: {a['url_content'][:100]}...")
        content = a.get("url_content") or ""
        print(f"📄 CONTENT: {content[:100]}...")

        print(a['url'])
        print("-" * 60)

    with open("defiant_articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(articles)} articles to defiant_articles.json")
