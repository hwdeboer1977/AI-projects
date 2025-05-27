import json
from datetime import datetime

# Paths
today_str = datetime.now().strftime("%m_%d_%Y")
input_path = f"Output_Twitter_05_22_2025/top_trending_tweets_labeled_{today_str}.json"
output_path = f"Output_Twitter_05_22_2025/top_trending_tweets_selected_{today_str}.json"

# Load tweets
with open(input_path, "r", encoding="utf-8") as f:
    tweets = json.load(f)

# Filter: keep tweets where all similar_tweets have sim ≤ 0.50
filtered = []
for tweet in tweets:
    if all(t["similarity"] <= 0.6 for t in tweet.get("similar_tweets", [])):
        filtered.append(tweet)

# Save output
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(filtered, f, indent=2, ensure_ascii=False)

print(f"Saved {len(filtered)} selected tweets to {output_path}")
