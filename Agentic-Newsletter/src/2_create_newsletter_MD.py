import json
from datetime import datetime

# === Settings ===
today_str = datetime.now().strftime("%m_%d_%Y")
date_str = today_str
#date_str = "06_12_2025"

# === File Paths ===
market_file = f"Output_Market_{date_str}/final_market_colour_text_{date_str}.json"
articles_file = f"Output_{date_str}/top_10_unique_articles_{date_str}.json"
#tweets_file = f"Output_Twitter_{date_str}/top10_tweets_clean_{date_str}.json"
fear_greed_img = f"Output_Market_{date_str}/fear_and_greed_index_{date_str}.png"
output_md = f"newsletter_{date_str}.md"

# === Load JSON Data ===
with open(market_file, "r", encoding="utf-8") as f:
    market_data = json.load(f)

with open(articles_file, "r", encoding="utf-8") as f:
    articles = json.load(f)

# with open(tweets_file, "r", encoding="utf-8") as f:
#     tweets = json.load(f)

# === Start Markdown Output ===
lines = []

# Nethermind's logo

lines.append(f'<img src="../src/logo.png" alt="Logo" width="100"/>\n')


# --- Market Colour ---
lines.append("# Daily Crypto Market Pulse")
lines.append(f"**Date:** {date_str.replace('_', '-')}\n")
lines.append("## Market Colour\n")
lines.append(market_data["market_colour"]["paragraph"] + "\n")
lines.append(market_data["etf_flows"]["summary"] + "\n")



# --- Top 5 Social Sentiment ---
lines.append("## 🐦 Top 5 Social Sentiment\n")
for i, article in enumerate(articles[:5], 1):
    title = article.get("title", "No title")
    url = article.get("url", "#")
    summary = article.get("summary", [])
    lines.append(f"### {i}. [{title}]({url})\n")
    for sentence in summary:
        lines.append(f"- {sentence.strip()}")
    lines.append("")


# --- Fear & Greed Index ---
lines.append("## 😨 Fear & Greed Index\n")
#lines.append(f"![Fear and Greed Index]({fear_greed_img})\n")
lines.append(f'<img src="../Output_Market_{date_str}/fear_and_greed_index_{date_str}.png" alt="Fear and Greed Index" width="300"/>\n')



# --- Top 5 News Articles ---
lines.append("## 🗞️ Top 5 News Articles\n")
for i, article in enumerate(articles[-5:], 1):
    title = article.get("title", "No title")
    url = article.get("url", "#")
    summary = article.get("summary", [])
    lines.append(f"### {i}. [{title}]({url})\n")
    for sentence in summary:
        lines.append(f"- {sentence.strip()}")
    lines.append("")


# === Save Markdown File ===
with open(output_md, "w", encoding="utf-8") as f:
    f.write("\n\n".join(lines))


print(f"Markdown newsletter saved to {output_md}")
