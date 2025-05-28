
# Information market colour
#/home/lupo1977/ai-agent-env/Output_Market_05_28_2025/final_market_colour_text_05_28_2025.json # text for newsletter
#/home/lupo1977/ai-agent-env/Output_Market_05_28_2025/fear_and_greed_index_05_28_2025.png # fear and greed index

# Information news articles
#/home/lupo1977/ai-agent-env/src/Summarize/logo.png # Nethermind's logo at top left of newsletter
#/home/lupo1977/ai-agent-env/Output_05_27_2025/top_10_unique_articles_05_27_2025.json # Summary articles

# Information twitter
#/home/lupo1977/ai-agent-env/Output_Twitter_05_27_2025/top10_tweets_clean_05_27_2025.json

import json
from datetime import datetime

# === Load market data ===
with open("Output_Market_05_28_2025/final_market_colour_text_05_28_2025.json", "r") as f:
    market_data = json.load(f)

# === Load article summaries ===
with open("Output_05_27_2025/top_10_unique_articles_05_27_2025.json", "r") as f:
    articles = json.load(f)

# === Load tweets ===
with open("Output_Twitter_05_27_2025/top10_tweets_clean_05_27_2025.json", "r") as f:
    tweets = json.load(f)

# === Build the newsletter object ===
newsletter = {
    "date": "05_28_2025",
    "header_logo": "src/Summarize/logo.png",
    "sections": {
        "market_colour": {
            "text": market_data["market_colour"]["paragraph"],
            "etf_summary": market_data["etf_flows"]["summary"],
            "fear_and_greed_image": "Output_Market_05_28_2025/fear_and_greed_index_05_28_2025.png"
        },
        "top_articles": articles,
        "top_tweets": tweets
    }
}

# === Save final newsletter to JSON ===
output_path = "newsletter_combined_05_28_2025.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(newsletter, f, indent=2)

print(f"✅ Combined newsletter saved to: {output_path}")
