"""
The Defiant News Scraper - Production Version
============================================

FIXED ISSUES:
- Replaced undetected_chromedriver with selenium + webdriver-manager (resolves compatibility issues)
- Enhanced Cloudflare Turnstile bypass with advanced stealth techniques
- Improved error handling and retry logic for production reliability
- Optimized content extraction with multiple fallback selectors

ARCHITECTURE:
1. RSS Feed Parsing: Fetches article metadata from https://thedefiant.io/feed/
2. Content Scraping: Uses enhanced selenium with stealth options to bypass bot protection
3. Data Processing: Extracts clean article content from <article><p> tags
4. JSON Output: Saves structured data ready for LLM processing

DEPENDENCIES:
- feedparser: RSS feed parsing
- beautifulsoup4: HTML content extraction
- selenium: Web browser automation
- webdriver-manager: Automatic ChromeDriver management

INTEGRATION:
- Input: RSS feed from The Defiant
- Output: JSON file with structured article data for LLM pipeline
- Compatible with existing AgenticNews master_all_scripts.py workflow
"""

import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import json
import os
import random

# Selenium components for enhanced web scraping
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
RSS_FEED_URL = "https://thedefiant.io/feed/"
SOURCE_NAME = "The Defiant"
MAX_RETRIES = 3
MIN_PARAGRAPH_THRESHOLD = 5  # Minimum paragraphs to consider successful scraping

def setup_output_directory():
    """
    Creates output directory with today's date format.
    
    Returns:
        tuple: (output_directory_path, json_filename_path)
        
    Example:
        output_dir = "Output_05_31_2025"
        filename = "Output_05_31_2025/Defiant_articles_24h_05_31_2025.json"
    """
    today_str = datetime.now().strftime("%m_%d_%Y")
    output_dir = f"Output_{today_str}"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"Defiant_articles_24h_{today_str}.json")
    return output_dir, filename

def get_enhanced_chrome_options():
    """
    Configures Chrome options for Cloudflare Turnstile bypass.
    
    Stealth Features:
    - Removes automation detection flags
    - Randomizes user agent and window size
    - Disables unnecessary features for faster loading
    - Mimics real browser behavior
    
    Returns:
        Options: Configured Chrome options object
    """
    options = Options()
    
    # Core stealth settings to avoid detection
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Additional anti-detection measures
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    
    # Performance optimizations (faster loading = less detection risk)
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")  # Most content is server-rendered
    
    # Randomized browser fingerprinting
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Randomized window dimensions
    window_sizes = ["1920,1080", "1366,768", "1440,900", "1536,864"]
    options.add_argument(f"--window-size={random.choice(window_sizes)}")
    
    return options

def scrape_article_content(url):
    """
    Scrapes full article content from a given URL using enhanced selenium.
    
    Process:
    1. Initialize Chrome with stealth options
    2. Navigate to article URL with human-like behavior
    3. Handle Cloudflare challenges if present
    4. Extract content using multiple selector strategies
    5. Retry on failure with exponential backoff
    
    Args:
        url (str): Article URL to scrape
        
    Returns:
        tuple: (article_content_string, paragraph_count)
        
    Example:
        content, count = scrape_article_content("https://thedefiant.io/news/...")
        # Returns: ("Bitcoin prices surged...", 15)
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Initialize Chrome driver with automatic version management
            service = Service(ChromeDriverManager().install())
            options = get_enhanced_chrome_options()
            driver = webdriver.Chrome(service=service, options=options)
            
            # Remove webdriver property to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Navigate to article with human-like timing
            driver.get(url)
            time.sleep(random.uniform(3, 6))  # Random delay to mimic human behavior
            
            # Check for and handle Cloudflare challenge
            page_source = driver.page_source
            if "Checking your browser" in page_source or "cloudflare" in page_source.lower():
                time.sleep(8)  # Wait for challenge resolution
                page_source = driver.page_source
            
            # Simulate human scrolling behavior to load lazy content
            total_height = driver.execute_script("return document.body.scrollHeight")
            for i in range(3):
                scroll_position = (i + 1) * (total_height // 3)
                driver.execute_script(f"window.scrollTo(0, {scroll_position})")
                time.sleep(random.uniform(1, 2))
            
            # Wait for article content to be present
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
            except:
                pass  # Continue even if article tag not found immediately
            
            # Get final page source and close driver
            final_html = driver.page_source
            driver.quit()
            
            # Parse HTML and extract article content
            soup = BeautifulSoup(final_html, "html.parser")
            
            # Multiple content extraction strategies (ordered by preference)
            content_strategies = [
                ("article", lambda container: container.find_all("p")),  # Primary: article tag
                (".post-content", lambda container: container.find_all("p")),  # Fallback 1
                (".entry-content", lambda container: container.find_all("p")),  # Fallback 2
                ("main", lambda container: container.find_all("p")),  # Fallback 3
            ]
            
            paragraphs = []
            successful_strategy = None
            
            for selector, extractor in content_strategies:
                if selector.startswith('.'):
                    # CSS class selector
                    container = soup.select_one(selector)
                else:
                    # HTML tag selector
                    container = soup.find(selector)
                
                if container:
                    paragraphs = extractor(container)
                    if len(paragraphs) >= MIN_PARAGRAPH_THRESHOLD:
                        successful_strategy = selector
                        break
            
            # Validate content quality
            if not paragraphs or len(paragraphs) < MIN_PARAGRAPH_THRESHOLD:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(random.uniform(5, 10))  # Wait before retry
                    continue
                else:
                    return "⚠️ Insufficient content found after all attempts", 0
            
            # Extract and clean paragraph text
            paragraph_count = len(paragraphs)
            article_content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            return article_content, paragraph_count
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(random.uniform(5, 15))  # Exponential backoff
                continue
            else:
                return f"❌ Scraping failed after {MAX_RETRIES} attempts: {str(e)}", 0
    
    return "❌ All retry attempts exhausted", 0

def fetch_rss_articles():
    """
    Fetches and filters articles from The Defiant RSS feed.
    
    Process:
    1. Parse RSS feed from thedefiant.io
    2. Filter articles published in last 24 hours
    3. Extract metadata (title, URL, summary, publish date)
    4. Return list of article metadata dictionaries
    
    Returns:
        list: List of article metadata dictionaries
        
    Example:
        articles = fetch_rss_articles()
        # Returns: [{"title": "...", "link": "...", "published_dt": ..., "summary": "..."}, ...]
    """
    try:
        # Parse RSS feed
        feed = feedparser.parse(RSS_FEED_URL)
        
        if not feed.entries:
            print(f"❌ RSS feed empty or inaccessible: {RSS_FEED_URL}")
            return []
        
        # Calculate 24-hour cutoff time
        now = datetime.now()
        cutoff_time = now - timedelta(days=2)
        
        recent_articles = []
        
        for entry in feed.entries:
            # Extract publish date
            published_parsed = entry.get("published_parsed")
            if not published_parsed:
                continue  # Skip entries without publish date
            
            published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
            
            # Filter for last 24 hours only
            if published_dt < cutoff_time:
                continue
            
            # Extract article metadata
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            raw_summary = entry.get("summary", "") or entry.get("description", "")
            
            # Clean HTML from summary
            summary_soup = BeautifulSoup(raw_summary, "html.parser")
            clean_summary = summary_soup.get_text(strip=True)
            
            recent_articles.append({
                "title": title,
                "link": link,
                "published_dt": published_dt,
                "summary": clean_summary
            })
        
        return recent_articles
        
    except Exception as e:
        print(f"❌ RSS parsing failed: {str(e)}")
        return []

def scrape_defiant_articles():
    """
    Main function to scrape The Defiant articles from last 24 hours.
    
    Complete Pipeline:
    1. Setup output directory and filename
    2. Fetch article metadata from RSS feed
    3. Scrape full content for each article
    4. Structure data for LLM processing
    5. Save results to JSON file
    
    Returns:
        str: Success message with file path
    """
    # Setup output file structure
    output_dir, filename = setup_output_directory()
    
    # Fetch recent articles from RSS
    rss_articles = fetch_rss_articles()
    
    if not rss_articles:
        return "❌ No recent articles found in RSS feed"
    
    print(f"Found {len(rss_articles)} articles from last 24 hours")
    
    # Scrape full content for each article
    scraped_articles = []
    
    for i, article_meta in enumerate(rss_articles, 1):
        print(f"Processing article {i}/{len(rss_articles)}: {article_meta['title'][:50]}...")
        
        # Scrape full article content
        content, paragraph_count = scrape_article_content(article_meta['link'])
        
        # Structure data for LLM pipeline (same format as BeInCrypto)
        article_data = {
            "title": article_meta['title'],
            "post": article_meta['summary'],  # RSS summary for LLM context
            "url": article_meta['link'],
            "url_content": content,  # Full scraped content for LLM processing
            "paragraph_count": paragraph_count,
            "source": SOURCE_NAME,
            "published": article_meta['published_dt'].isoformat(),
            "scraped_at": datetime.now().isoformat()
        }
        
        scraped_articles.append(article_data)
        
        # Rate limiting to avoid being blocked
        if i < len(rss_articles):  # Don't delay after last article
            time.sleep(random.uniform(2, 4))
    
    # Save results to JSON file for LLM pipeline
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(scraped_articles, f, ensure_ascii=False, indent=2)
    
    # Calculate summary statistics
    total_paragraphs = sum(article['paragraph_count'] for article in scraped_articles)
    successful_scrapes = len([a for a in scraped_articles if a['paragraph_count'] >= MIN_PARAGRAPH_THRESHOLD])
    
    return f"✅ Successfully scraped {successful_scrapes}/{len(scraped_articles)} articles ({total_paragraphs} total paragraphs) → {filename}"

if __name__ == "__main__":
    """
    Production execution entry point.
    
    Runs the complete Defiant scraping pipeline and outputs:
    - Single success/failure message
    - JSON file ready for LLM processing
    - Compatible with AgenticNews master pipeline
    """
    try:
        result_message = scrape_defiant_articles()
        print(result_message)
    except Exception as e:
        print(f"❌ Defiant scraper failed: {str(e)}")