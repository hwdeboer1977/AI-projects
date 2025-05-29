# Agentic News Newsletter Generator

This project is a fully automated pipeline for generating a daily crypto newsletter. It scrapes the latest crypto news, analyzes market trends, summarizes Twitter engagement, and outputs the final newsletter in multiple formats (JSON, Markdown, and HTML).

---

## Features

- Scrapes articles from top crypto sites (e.g., CoinDesk, The Block, Decrypt, BeInCrypto, etc.)
- Extracts and summarizes key content using LLM agents
- Tracks market data (Chainlink prices, ETF flows, Fear & Greed index)
- Summarizes and ranks Twitter posts from leading accounts
- Outputs a clean, readable newsletter in JSON / Markdown / HTML / PDF formats

---

## Project Structure

```text
src/
│
├── Scraping/ -> Scraping news articles and tweets
├── Articles_Summarize/ -> Agents to summarize news articles and remove articles with similar content
├── Twitter_summarize/ -> Agents to select and format tweets
├── Market/ -> Scripts for BTC/ETH price feed, ETF flows etc
├── Output*/ -> Folder with all the output files from the scripts aboce
│
├── 1_create_newsletter_JSON.py 
├── 2_create_newsletter_MD.py
├── 3_create_newsletter_HTML.py
│
├── master_all_scripts.py -> Runs all scripts above at once
```
---

## Installation

Make sure you have Python 3.10+ installed and install dependencies
