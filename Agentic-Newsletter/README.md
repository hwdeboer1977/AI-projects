# Agentic News Newsletter Generator

This project is a fully automated pipeline for generating a daily crypto newsletter. It scrapes the latest crypto news, analyzes market trends, summarizes Twitter engagement, and outputs the final newsletter in multiple formats (JSON, Markdown, HTML, and PDF). Results can also be stored in PostgreSQL and published to Notion.

---

## Features

- Scrapes articles from top crypto sites (CoinDesk, The Block, Decrypt, BeInCrypto, Blockworks, Cointelegraph, Bankless, The Defiant)
- Extracts and summarizes key content using LLM agents, and removes near-duplicate articles
- Tracks market data (Chainlink BTC/ETH prices, ETF flows, Fear & Greed index)
- Summarizes and ranks Twitter/X posts from leading accounts
- Outputs a clean, readable newsletter in JSON / Markdown / HTML / PDF formats
- Optional persistence to PostgreSQL and publishing to Notion

---

## Project Structure

```text
.
├── master_all_scripts.py      -> Orchestrates the full pipeline (scrape -> summarize -> render)
├── production_scraping.py      -> Standalone unified scraper (all sources + Twitter in one file)
├── save_news_DB.py             -> Loads generated newsletter JSON into PostgreSQL
│
└── src/
    ├── Scraping/               -> Per-source news scrapers + Twitter agents
    ├── Articles_Summarize/     -> Agents to summarize articles and drop overlapping content
    ├── Twitter_summarize/      -> Agents to select, rank, and format tweets
    ├── Market/                 -> BTC/ETH price feed, ETF flows, Fear & Greed, market colour text
    ├── Notion/                 -> Resize images and upload the newsletter to Notion
    ├── ChromaDB/               -> Vector store used for de-duplication / retrieval
    │
    ├── 1_create_newsletter_JSON.py
    ├── 2_create_newsletter_MD.py
    └── 3_create_newsletter_HTML.py
```

> Note: `Output*/` folders are produced at runtime and are git-ignored, so they will not be present after a fresh clone.

---

## Installation

Make sure you have **Python 3.10+** installed, then set up a virtual environment and install the dependencies:

```bash
# Clone and enter the project
cd Agentic-Newsletter

# Create and activate a virtual environment
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Playwright-based scrapers also need browser binaries:
playwright install
```

The scrapers rely on a Chrome/Chromium browser being available on the system (via Selenium / `undetected-chromedriver` / Playwright).

---

## Configuration

Configuration is read from environment variables. Create a `.env` file in the project root (it is git-ignored) and set the keys you need. Not every key is required — only set the ones for the sources and integrations you actually use.

```dotenv
# LLM
OPENAI_API_KEY=

# News / market data providers
NEWSAPI_KEY=
CRYPTOCOMPARE_KEY=
ALCHEMY_API_KEY=
SOSOVALUE_API_KEY_HW=

# Twitter / X
TWITTER_BEARER_TOKEN=
TWITTER_IO_API=

# Persistence & publishing
DATABASE_URL=               # PostgreSQL DSN, e.g. postgresql://postgres:<password>@localhost:5432/agent_db
AGENTIC_DATABASE_API=       # PostgreSQL connection / credentials (used elsewhere in the pipeline)
AGENTIC_NOTION_API=         # Notion integration token

# Pipeline toggles / limits (optional)
ENABLE_SELENIUM=true
ENABLE_TWITTER_API=true
MAX_ARTICLES_PER_SOURCE=25
TWITTER_MAX_TWEETS_PER_ACCOUNT=20
REQUEST_TIMEOUT=30
```

> Security note: do not hardcode secrets (API keys, database passwords) in source files. Load them from the environment / `.env` instead.

---

## Usage

### Run the full pipeline

```bash
python master_all_scripts.py
```

This orchestrates the stages in order: scrape news, scrape Twitter, build the market colour section, summarize articles and tweets, and render the final newsletter. Individual stages can be enabled/disabled by editing the `run_scripts(...)` blocks in `master_all_scripts.py`.

### Run the unified scraper only

```bash
python production_scraping.py
```

A self-contained scraper that aggregates all sources (plus Twitter) with quality scoring, deduplication, and 24-hour time filtering.

### Render a specific output format

```bash
python src/1_create_newsletter_JSON.py
python src/2_create_newsletter_MD.py
python src/3_create_newsletter_HTML.py
```

### Store results in PostgreSQL

```bash
python save_news_DB.py
```

Reads the generated `newsletter_combined_*.json` files and upserts them into the `newsletters` / `articles` tables.

### Publish to Notion

```bash
python src/Notion/master_upload_notion.py
```

---

## Requirements

Key third-party libraries used across the project:

- **LLM / agents:** `openai`, `openai-agents`
- **Scraping:** `requests`, `beautifulsoup4`, `feedparser`, `selenium`, `undetected-chromedriver`, `webdriver-manager`, `playwright`, `playwright-stealth`
- **Data / ML:** `numpy`, `scikit-learn`, `chromadb`
- **Blockchain / market:** `web3`
- **Output & storage:** `markdown`, `Pillow`, `psycopg2-binary`
- **Utilities:** `python-dotenv`, `python-dateutil`, `typing-extensions`

---

## License

See the repository root for licensing information.
