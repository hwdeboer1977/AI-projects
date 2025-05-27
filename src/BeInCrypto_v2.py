import feedparser # Parses RSS feeds
from bs4 import BeautifulSoup # For HTML parsing
from playwright.sync_api import sync_playwright # Controls headless browser (sync version)
from playwright_stealth import stealth_sync # Hides automation fingerprints
from datetime import datetime, timedelta # Handles date/time operations
import time # Converts struct_time from RSS to datetime
import json # Saves output as JSON
import os


# Combines RSS and full scraping: Efficient 24h filtering from RSS + full article scrape using Playwright.

# Format today's date
today_str = datetime.now().strftime("%m_%d_%Y")

# Create folder for today (e.g. Output_05_26_2025)
output_dir = f"Output_{today_str}"
os.makedirs(output_dir, exist_ok=True)

# Set filename path inside that folder
filename = os.path.join(output_dir, f"BeInCrypto_articles_24h_{today_str}.json")

# Full content scraper using Playwright for BeInCrypto articles
def get_url_content_playwright_beincrypto(url):
    try:
        # Launch headless Chromium browser
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # Set up a browser context with a spoofed user-agent and headers
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                            (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.google.com"
                }
            )
            
            # Open new browser page
            page = context.new_page()
            stealth_sync(page) # Apply stealth settings to the page

            # Navigate to the URL and wait for the body to load
            page.goto(url, timeout=60000)
            page.wait_for_selector("body", timeout=20000)

            # Scroll to bottom to ensure lazy-loaded content appears
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)

            # Get full HTML content of the page
            html = page.content()
            browser.close()

            # Parse the HTML and extract paragraphs from the main article content
            soup = BeautifulSoup(html, "html.parser")
            container = soup.select_one("div.entry-content")  # BeInCrypto's main article body
            paragraphs = container.find_all("p") if container else []
            paragraph_count = len(paragraphs)

            # For now we limit to 12 paragraphs
            # return (
            #     "\n".join(p.get_text(strip=True) for p in paragraphs[:12]) if paragraphs else "No entry-content <p> tags found",
            #     paragraph_count
            # )

            return (
                "\n".join(p.get_text(strip=True) for p in paragraphs) if paragraphs else "No entry-content <p> tags found",
                paragraph_count
            )

    # Handle browser or parsing errors
    except Exception as e:
        return f"❌ Stealth Playwright error: {e}"

# RSS + Scrape + Save function: fetch BeInCrypto articles from last 24h
def fetch_beincrypto_last_24h():
    url = "https://beincrypto.com/feed/" # BeInCrypto RSS feed URL
    feed = feedparser.parse(url) # Parse the RSS feed
    articles = []  # List to store extracted article data

    now = datetime.utcnow()
    cutoff = now - timedelta(days=1) # Filter only articles from the last 24 hours

    for entry in feed.entries:
        published_parsed = entry.get("published_parsed")
        if not published_parsed:
            continue

        # Convert RSS time format to datetime
        published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
        if published_dt < cutoff:
            continue  # Skip articles without a valid timestamp

        # Extract metadata
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        raw_description = entry.get("summary", "") or entry.get("description", "")
        soup = BeautifulSoup(raw_description, "html.parser")
        post = soup.get_text(strip=True)  # Clean description text

        print(f"[{published_dt}] Fetching: {title}")

        # Fetch full article content via Playwright
        url_content, paragraph_count = get_url_content_playwright_beincrypto(link)

        # Store the result
        articles.append({
            "title": title,
            "post": post,
            "url": link,
            "views": None, # Placeholder (could be populated later)
            "reposts": None, # Placeholder (could be populated later)
            "url_content": url_content,
            "paragraph_count": paragraph_count,  
            "source": "BeInCrypto",
            "published": published_dt.isoformat()
        })

    return articles

# Run + save
if __name__ == "__main__":
    # Run the fetch function
    articles = fetch_beincrypto_last_24h()

    # Display each article in console
    for i, a in enumerate(articles, 1):
        print(f"[{i}] {a['title']}")
        print(f"Published: {a['published']}")
        print(f"Full content: {a['url_content'][:500]}...") # Preview first 500 characters
        print(f"Paragraphs: {a['paragraph_count']}")
        print(f"{a['url']}")
        print("-" * 60)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")
