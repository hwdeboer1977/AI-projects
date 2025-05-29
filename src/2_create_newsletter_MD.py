import json
from datetime import datetime

# === Settings ===
today_str = datetime.now().strftime("%m_%d_%Y")
date_str = today_str
#date_str_old = "05_28_2025"

# === File Paths ===
market_file = f"Output_Market_{date_str}/final_market_colour_text_{date_str}.json"
articles_file = f"Output_{date_str}/top_10_unique_articles_{date_str}.json"
tweets_file = f"Output_Twitter_{date_str}/top10_tweets_clean_{date_str}.json"
fear_greed_img = f"Output_Market_{date_str}/fear_and_greed_index_{date_str}.png"
output_md = f"newsletter_{date_str}.md"

# === Load JSON Data ===
with open(market_file, "r", encoding="utf-8") as f:
    market_data = json.load(f)

with open(articles_file, "r", encoding="utf-8") as f:
    articles = json.load(f)

with open(tweets_file, "r", encoding="utf-8") as f:
    tweets = json.load(f)

# === Start Markdown Output ===
lines = []

# --- Market Colour ---
lines.append("# Daily Crypto Market Pulse")
lines.append(f"**Date:** {date_str.replace('_', '-')}\n")
lines.append("## Market Colour\n")
lines.append(market_data["market_colour"]["paragraph"] + "\n")
lines.append(market_data["etf_flows"]["summary"] + "\n")

# --- Fear & Greed Index ---
lines.append("## 😨 Fear & Greed Index\n")
#lines.append(f"![Fear and Greed Index]({fear_greed_img})\n")
lines.append(f'<img src="{fear_greed_img}" alt="Fear and Greed Index" width="300"/>\n')

# --- Top 10 News Articles ---
lines.append("## 🗞️ Top 10 News Articles\n")
for i, article in enumerate(articles, 1):
    title = article.get("title", "No title")
    url = article.get("url", "#")
    summary = article.get("summary", "")

    lines.append(f"### {i}. [{title}]({url})\n")
    for sentence in summary:
        lines.append(f"- {sentence.strip()}")
    lines.append("")  # blank line


# --- Top 10 Tweets ---
lines.append("## 🐦 Top 10 Crypto Tweets\n")
for i, tweet in enumerate(tweets, 1):
    post = tweet["post"].strip().replace("\n", " ")
    url = tweet["url"]
    
    # First sentence as heading
    lines.append(f"### {i}. {post}")
    lines.append(f"[🔗 View Tweet]({url})\n")

# === Save Markdown File ===
with open(output_md, "w", encoding="utf-8") as f:
    f.write("\n\n".join(lines))


print(f"Markdown newsletter saved to {output_md}")
