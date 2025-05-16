from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_cointelegraph_with_playwright():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto("https://cointelegraph.com/", timeout=60000)  # 60 seconds
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    # Find headlines using href pattern or class name
    articles = soup.select("a[href^='/news/']")

    seen = set()
    results = []
    for a in articles:
        title = a.get_text(strip=True)
        href = a.get("href")

        if title and href not in seen and href.startswith("/news/"):
            seen.add(href)
            results.append({
                "title": title,
                "link": "https://cointelegraph.com" + href
            })
        if len(results) >= 5:
            break

    return results

# Test run
if __name__ == "__main__":
    headlines = scrape_cointelegraph_with_playwright()
    for i, h in enumerate(headlines, 1):
        print(f"[{i}] {h['title']}")
        print(h['link'])
        print("-" * 60)
