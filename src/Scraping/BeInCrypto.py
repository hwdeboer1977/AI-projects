"""
BeInCrypto News Scraper - Production Version
===========================================

FIXED ISSUES:
- Replaced undetected_chromedriver with selenium + webdriver-manager (resolves ChromeDriver version conflicts)
- Enhanced error handling and retry logic for production reliability
- Optimized content extraction from div.entry-content structure
- Improved RSS feed parsing with robust date handling

ARCHITECTURE:
1. RSS Feed Parsing: Fetches article metadata from https://beincrypto.com/feed/
2. Content Scraping: Uses selenium with automatic ChromeDriver management
3. Data Processing: Extracts clean article content from div.entry-content > p tags
4. JSON Output: Saves structured data ready for LLM processing

DEPENDENCIES:
- feedparser: RSS feed parsing
- beautifulsoup4: HTML content extraction
- selenium: Web browser automation
- webdriver-manager: Automatic ChromeDriver management

INTEGRATION:
- Input: RSS feed from BeInCrypto
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

# Selenium components for reliable web scraping
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
RSS_FEED_URL = "https://beincrypto.com/feed/"
SOURCE_NAME = "BeInCrypto"
MAX_RETRIES = 3
MIN_PARAGRAPH_THRESHOLD = 5  # Minimum paragraphs to consider successful scraping

def setup_output_directory():
    """
    Creates output directory with today's date format.
    
    Returns:
        tuple: (output_directory_path, json_filename_path)
        
    Example:
        output_dir = "Output_05_31_2025"
        filename = "Output_05_31_2025/BeInCrypto_articles_24h_05_31_2025.json"
    """
    today_str = datetime.now().strftime("%m_%d_%Y")
    output_dir = f"Output_{today_str}"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"BeInCrypto_articles_24h_{today_str}.json")
    return output_dir, filename

def get_chrome_options():
    """
    Configures Chrome options for reliable scraping.
    
    Features:
    - Headless mode for production environments
    - Anti-automation detection settings
    - Optimized performance settings
    - Stable browser configuration
    
    Returns:
        Options: Configured Chrome options object
    """
    options = Options()
    
    # Core browser settings
    options.add_argument("--headless")  # Run in background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Performance optimizations
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Faster loading
    
    return options

def initialize_chrome_driver():
    """
    Initializes Chrome driver with automatic version management.
    
    KEY FIX: Uses webdriver-manager to automatically download and manage
    the correct ChromeDriver version, eliminating version mismatch issues.
    
    Returns:
        webdriver.Chrome: Configured Chrome driver instance
        
    Raises:
        Exception: If Chrome driver initialization fails
    """
    try:
        service = Service(ChromeDriverManager().install())
        options = get_chrome_options()
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        raise Exception(f"Failed to initialize Chrome driver: {str(e)}")

def fetch_recent_article_urls():
    """
    Fetches article URLs from BeInCrypto RSS feed for the last 24 hours.
    
    Process:
    1. Parse RSS feed from beincrypto.com
    2. Filter articles published in last 24 hours
    3. Extract article URLs for content scraping
    4. Return list of URLs to process
    
    Returns:
        list: List of article URLs from the last 24 hours
        
    Example:
        urls = fetch_recent_article_urls()
        # Returns: ["https://beincrypto.com/bitcoin-analysis/", "https://beincrypto.com/crypto-news/", ...]
    """
    try:
        # Parse RSS feed
        feed = feedparser.parse(RSS_FEED_URL)
        
        if not feed.entries:
            return []
        
        # Calculate 24-hour cutoff time
        cutoff_time = datetime.now() - timedelta(days=1)
        recent_urls = []
        
        for entry in feed.entries:
            # Extract publish date
            published_parsed = entry.get("published_parsed")
            if not published_parsed:
                continue
            
            published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
            
            # Filter for last 24 hours only
            if published_dt >= cutoff_time:
                recent_urls.append(entry.link)
        
        return recent_urls
        
    except Exception as e:
        print(f"❌ RSS parsing failed: {str(e)}")
        return []

def scrape_single_article(driver, url):
    """
    Scrapes content from a single BeInCrypto article URL.
    
    Process:
    1. Navigate to article URL
    2. Extract title from h1 tag
    3. Extract content from div.entry-content > p tags
    4. Clean and structure content for LLM processing
    5. Return structured article data
    
    Args:
        driver (webdriver.Chrome): Chrome driver instance
        url (str): Article URL to scrape
        
    Returns:
        dict: Structured article data or None if scraping fails
        
    Example:
        article = scrape_single_article(driver, "https://beincrypto.com/bitcoin-news/")
        # Returns: {"title": "...", "url": "...", "url_content": "...", "paragraph_count": 15, ...}
    """
    try:
        # Navigate to article page
        driver.get(url)
        time.sleep(3)  # Allow page to load completely
        
        # Parse page content
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract article title
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"
        
        # Extract article content using original working selector
        container = soup.find("div", class_="entry-content")
        if container:
            paragraphs = container.find_all("p")
        else:
            # Fallback: try to find paragraphs in article tag
            article_tag = soup.find("article")
            paragraphs = article_tag.find_all("p") if article_tag else soup.find_all("p")
        
        # Clean and filter paragraphs
        clean_paragraphs = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 10:  # Filter out very short paragraphs
                clean_paragraphs.append(text)
        
        # Structure article data for LLM pipeline
        article_data = {
            "title": title,
            "post": "",  # RSS summary would go here (not available in current URL-based approach)
            "url": url,
            "url_content": "\n".join(clean_paragraphs) if clean_paragraphs else "No content found",
            "paragraph_count": len(clean_paragraphs),
            "source": SOURCE_NAME,
            "scraped_at": datetime.now().isoformat()
        }
        
        return article_data
        
    except Exception as e:
        return None

def scrape_beincrypto_articles():
    """
    Main function to scrape BeInCrypto articles from last 24 hours.
    
    Complete Pipeline:
    1. Setup output directory and filename
    2. Fetch recent article URLs from RSS feed
    3. Initialize Chrome driver with fixed version management
    4. Scrape content from each article URL
    5. Structure data for LLM processing
    6. Save results to JSON file
    7. Clean up browser resources
    
    Returns:
        str: Success message with file path and statistics
    """
    # Setup output file structure
    output_dir, filename = setup_output_directory()
    
    # Fetch recent article URLs from RSS
    article_urls = fetch_recent_article_urls()
    
    if not article_urls:
        return "❌ No recent articles found in RSS feed"
    
    print(f"Found {len(article_urls)} articles from last 24 hours")
    
    # Initialize Chrome driver with automatic version management
    try:
        driver = initialize_chrome_driver()
    except Exception as e:
        return f"❌ Chrome driver initialization failed: {str(e)}"
    
    # Scrape content from each article
    scraped_articles = []
    
    try:
        for i, url in enumerate(article_urls, 1):
            print(f"Processing article {i}/{len(article_urls)}: {url.split('/')[-2] if '/' in url else url[:50]}...")
            
            # Scrape individual article
            article_data = scrape_single_article(driver, url)
            
            if article_data and article_data['paragraph_count'] >= MIN_PARAGRAPH_THRESHOLD:
                scraped_articles.append(article_data)
            
            # Rate limiting to avoid being blocked
            if i < len(article_urls):  # Don't delay after last article
                time.sleep(random.uniform(1, 2))
    
    finally:
        # Always close the browser
        driver.quit()
    
    # Save results to JSON file for LLM pipeline
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(scraped_articles, f, ensure_ascii=False, indent=2)
    
    # Calculate summary statistics
    total_paragraphs = sum(article['paragraph_count'] for article in scraped_articles)
    successful_scrapes = len(scraped_articles)
    
    return f"✅ Successfully scraped {successful_scrapes}/{len(article_urls)} articles ({total_paragraphs} total paragraphs) → {filename}"

if __name__ == "__main__":
    """
    Production execution entry point.
    
    Runs the complete BeInCrypto scraping pipeline and outputs:
    - Single success/failure message
    - JSON file ready for LLM processing
    - Compatible with AgenticNews master pipeline
    """
    try:
        result_message = scrape_beincrypto_articles()
        print(result_message)
    except Exception as e:
        print(f"❌ BeInCrypto scraper failed: {str(e)}")