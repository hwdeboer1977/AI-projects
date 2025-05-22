import undetected_chromedriver as uc  # Headless browser that bypasses bot detection
from bs4 import BeautifulSoup         # For parsing HTML content
from datetime import datetime, timedelta, timezone  # For time filtering
import time                           # For sleeps between requests
import json                           # To save the scraped output
import os                             # For file handling

# Blockworks News Scraper
# Method: Headless browser scraping using undetected-chromedriver (UDC)
# No RSS feed available — article links are scraped directly from the /news page
# Each article page is visited in a headless Chrome session
# Content includes title, description, full body text (from <article><p>) and timestamp

# Base and news listing URLs
BASE_URL = "https://blockworks.co"
NEWS_URL = "https://blockworks.co/news"

# Calculate the cutoff time for 24h filter (aware datetime)
CUTOFF_TIME = datetime.now(timezone.utc) - timedelta(days=1)

# Format today's date for the output filename
today_str = datetime.now().strftime("%m_%d_%Y")
filename = f"Blockworks_articles_24h_{today_str}.json"


# Utility: Fetch page HTML using UDC with optional debugging
def fetch_html_with_udc(url, debug_name=None, wait_time=5):
    # Setup undetected Chrome options
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=en-US,en;q=0.9")

    # Start headless browser
    driver = uc.Chrome(options=options)
    print(f"Visiting: {url}")
    driver.get(url)
    time.sleep(wait_time)  # Allow time for dynamic content to load
    
    # Get HTML content and quit
    html = driver.page_source
    driver.quit()

    # Optionally save HTML for debugging
    if debug_name:
        os.makedirs("debug", exist_ok=True)
        with open(f"debug/{debug_name}.html", "w", encoding="utf-8") as f:
            f.write(html)

    return html

    

# Scrape full article content from one article page
def get_article_data(url, debug=False):
    try:
        html = fetch_html_with_udc(url, debug_name="blockworks_article" if debug else None)

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # Extract publish time
        time_tag = soup.find("time")
        published = time_tag.get("datetime") if time_tag else None
        published_dt = None
        if published:
            try:
                published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except:
                published_dt = None

        # Skip if article is older than 24 hours or time is missing
        if not published_dt or published_dt < CUTOFF_TIME:
            print(f"⏱ Skipped: older than 24h or no time found → {published_dt}")
            return None

        # Extract short description from meta tag
        meta_desc = soup.find("meta", {"name": "description"})
        post = meta_desc["content"].strip() if meta_desc and meta_desc.has_attr("content") else ""

        # Extract full article body from <article><p>
        paragraphs = soup.select("article p")
        paragraph_count = len(paragraphs)
        url_content = "\n".join(p.get_text(strip=True) for p in paragraphs) if paragraphs else "⚠️ No <p> tags found"

        return {
            "url": url,
            "source": "Blockworks",
            "published": published_dt.isoformat(),
            "title": title,
            "post": post,
            "url_content": url_content,
            "paragraph_count": paragraph_count
        }

    except Exception as e:
        return {
            "url": url,
            "source": "Blockworks",
            "title": "UDC Error",
            "post": "",
            "url_content": f"UDC error: {e}"
        }

# Load latest article URLs from the main news page
def get_recent_blockworks_urls():
    html = fetch_html_with_udc(NEWS_URL)
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

# Run the scraper
if __name__ == "__main__":
    DEBUG = False

    # Get recent article URLs from listing page
    urls = get_recent_blockworks_urls()
    articles = []

     # Scrape each article
    for url in urls:
        article = get_article_data(url, debug=DEBUG)

        # If it's older than 24h, stop crawling further
        if article is None:
            print("Stopping — article is older than 24h.")
            break # Stop visiting further URLs

        articles.append(article)
        time.sleep(1) # Rate limit between requests

    # Save result to JSON
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n Saved {len(articles)} articles to {filename}")
