import os
from datetime import datetime

# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
date_str = today_str
#date_str = "06_12_2025"

import json
from datetime import datetime

# === Load market data ===
with open(f"Output_Market_{date_str}/final_market_colour_text_{date_str}.json", "r") as f:
    market_data = json.load(f)

# === Load article summaries ===
with open(f"Output_{date_str}/top_10_unique_articles_{date_str}.json", "r") as f:
    articles = json.load(f)

# # === Load tweets ===
# with open(f"Output_Twitter_{date_str}/top10_tweets_clean_{date_str}.json", "r") as f:
#     tweets = json.load(f)

# === Build the newsletter object ===
newsletter = {
    "date": date_str,
    "header_logo": f"../src/Summarize/logo.png",
    "sections": {
        "market_colour": {
            "text": market_data["market_colour"]["paragraph"],
            "etf_summary": market_data["etf_flows"]["summary"],
            "fear_and_greed_image": f"../Output_Market_{date_str}/fear_and_greed_index_{date_str}.png"
        },
        "top_articles": articles,
        #"top_tweets": tweets
    }
}


# === Save final newsletter to JSON ===
output_path = f"newsletter_combined_{date_str}.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(newsletter, f, indent=2)

print(f"Combined newsletter saved to: {output_path}")
