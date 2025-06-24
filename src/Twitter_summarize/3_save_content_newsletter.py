import json
from datetime import datetime


# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
date_str = today_str
#date_str = "05_22_2025"

input_path = f"Output_Twitter_{date_str}/top_trending_tweets_selected_{date_str}.json"
output_json = f"Output_Twitter_{date_str}/top10_tweets_brief_{date_str}.json"

# Load full tweets
with open(input_path, "r", encoding="utf-8") as f:
    tweets = json.load(f)

# Sort by engagement_score and select top 10
top_10 = sorted(tweets, key=lambda x: x.get("engagement_score", 0), reverse=True)[:10]

# Reduce to only post and url
minimal_data = [{"post": tweet["text"], "url": tweet["url"], "article_link": tweet["article_link"]} for tweet in top_10]

# Save valid JSON
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(minimal_data, f, indent=2, ensure_ascii=False)

print(f"Saved simplified JSON to {output_json}")
