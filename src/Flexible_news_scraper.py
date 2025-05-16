
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_news_site(name, url, base_url, selector, limit=5):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select(selector)
    print(f"{name}: found {len(articles)} matching elements")

    seen = set()
    results = []
    for a in articles:
        title = a.get_text(strip=True)
        href = a.get("href")

        if title and href and href not in seen and href.startswith("/"):
            seen.add(href)
            results.append({
                "source": name,
                "title": title,
                "link": base_url + href
            })
        if len(results) >= limit:
            break

    return results

if __name__ == "__main__":
    sources = [
        # {
        #     "name": "Cointelegraph",
        #     "url": "https://cointelegraph.com/",
        #     "base_url": "https://cointelegraph.com",
        #     "selector": "a[href^='/news/']"
        # },
        # {
        #     "name": "Blockworks",
        #     "url": "https://blockworks.co/news",
        #     "base_url": "https://blockworks.co",
        #     "selector": "a[href^='/news/']"
        # },
        # {
        #     "name": "The Defiant",
        #     "url": "https://thedefiant.io/latest",
        #     "base_url": "https://thedefiant.io",
        #     "selector": "a[href^='/']"
        # },
        {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com/news/",
            "base_url": "https://www.coindesk.com",
            "selector": "article a[href^='/']"
        }

    ]

    all_articles = []
    for site in sources:
        print(f"Fetching from {site['name']}...")
        try:
            articles = scrape_news_site(site["name"], site["url"], site["base_url"], site["selector"])
            all_articles.extend(articles)
        except Exception as e:
            print(f"Failed to scrape {site['name']}: {{e}}")

    for i, a in enumerate(all_articles, 1):
        print(f"[{i}] [{a['source']}] {a['title']}")
        print(a['link'])
        print("-" * 60)
