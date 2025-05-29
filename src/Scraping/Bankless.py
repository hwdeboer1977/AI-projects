# Import required libraries
from playwright.sync_api import sync_playwright             # For headless browser automation
from bs4 import BeautifulSoup                               # For HTML parsing
from datetime import datetime, timedelta, timezone          # For timestamp handling
from dateutil import parser                                 # For parsing various datetime formats
import json                                                 # For saving the output
import time                                                 # For optional delays
import os                                                   # For file and folder handling

# Bankless does not publish many articles in 24 hours, so less relevant
# Henk: As of 29-5-2025 the script is not scraping content anymore?

# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")


# Create folder for today (e.g. Output_05_26_2025)
output_dir = f"Output_{today_str}"
os.makedirs(output_dir, exist_ok=True)

# Set filename path inside that folder
filename = os.path.join(output_dir, f"Bankless_articles_24h_{today_str}.json")


def scrape_bankless_articles(limit=5): 
    results = [] # List to store article dictionaries
    seen = set() # Track already visited links to avoid duplicates
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1) # Cutoff time: 24 hours ago

     # Start a headless browser session using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Use Chromium in headless mode
        context = browser.new_context()
        page = context.new_page()
        
        # Go to the Bankless published articles page
        page.goto("https://www.bankless.com/read", timeout=60000)
        page.wait_for_timeout(3000) # Wait for 3 seconds to ensure the page is loaded
 
        # Parse the page HTML
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Select all internal links (href starts with '/')
        links = soup.select("a[href^='/']")

        for link in links:
            href = link.get("href")
            full_url = "https://www.bankless.com" + href
            title = link.get_text(strip=True)

            # Skip links that are already seen or are invalid
            if not href or not title or href in seen or not href.startswith("/"):
                continue
            seen.add(href)

            print(f"Scraping: {title}")

            # Open the article page in a new tab
            article_page = context.new_page()
            article_page.goto(full_url, timeout=60000)
            article_page.wait_for_timeout(3000)

            article_html = article_page.content()
            article_soup = BeautifulSoup(article_html, "html.parser")

            # Try to extract the published timestamp
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

            # Skip article if timestamp is missing or older than 24 hours
            if not published_dt or published_dt < cutoff:
                article_page.close()
                continue

            # Extract summary from meta description or fallback to first paragraph
            meta_desc = article_soup.find("meta", {"name": "description"})
            post = meta_desc.get("content", "").strip() if meta_desc else ""
            if not post:
                first_para = article_soup.select_one("article p")
                post = first_para.get_text(strip=True) if first_para else ""

            # Extract full article content by gathering all <p> tags inside the article body
            prose = article_soup.select_one("article") or article_soup.select_one("div.prose")
            paragraphs = prose.find_all("p") if prose else []
            paragraph_count = len(paragraphs)
            url_content = "\n".join(p.get_text(strip=True) for p in paragraphs) or "⚠️ No content found"

            article_page.close()

            # Store the extracted data in a dictionary
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

            # Stop if we have reached the desired limit
            if len(results) >= limit:
                break

        browser.close()
    return results


# Main logic for execution
if __name__ == "__main__":
    # Scrape up to 10 recent articles
    articles = scrape_bankless_articles(limit=10)

    # Print summary of each article to console
    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"Published: {a['published']}")
        print(f"Summary: {a['post'][:100]}...")
        print(f"Content: {a['url_content'][:500]}...")
        print(f"Paragraphs: {a['paragraph_count']}")
        print(f"{a['url']}")
        print("-" * 60)

    # Save results to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")