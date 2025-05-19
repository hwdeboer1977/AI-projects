from playwright.sync_api import sync_playwright
import json

# I cant get post and url_content from website
# The Block's homepage does not include timestamps for each article?

def scrape_theblock(limit=5):
    results = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()

        page.goto("https://www.theblock.co/latest-crypto-news", timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # 🔍 Find article links using live DOM
        links = page.query_selector_all("a[href^='/post/']")
        print(f"🔗 Found {len(links)} links")

        for link in links:
            href = link.get_attribute("href")
            title = link.inner_text().strip()

            if not title or not href or href in seen:
                continue

            seen.add(href)
            full_url = "https://www.theblock.co" + href

            # Open article page in a new tab
            article_page = context.new_page()
            article_page.goto(full_url, timeout=60000)
            article_page.wait_for_load_state("networkidle")
            article_page.wait_for_timeout(2000)
            #article_page.wait_for_selector("article p", timeout=10000)


            # Get meta description
            meta_desc = article_page.query_selector("meta[name='description']")
            print(f"[meta_desc element] {meta_desc}")
            post = meta_desc.get_attribute("content") if meta_desc else ""
        

            # Get full content from article body
            paragraphs = article_page.query_selector_all("article p")
            url_content = "\n".join(p.inner_text().strip() for p in paragraphs[:5])  # First few paragraphs

            article_page.close()

            results.append({
                "title": title,
                "post": post,
                "url": full_url,
                "views": None,
                "reposts": None,
                "url_content": url_content,
                "source": "TheBlock"
            })

            if len(results) >= limit:
                break

        browser.close()

    return results

# Run and save
if __name__ == "__main__":
    articles = scrape_theblock(limit=5)

    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"📰 {a['post'][:120]}...")
        print(a['url'])
        print("-" * 60)

    with open("theblock_articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
