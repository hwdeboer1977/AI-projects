import json
import re
from datetime import datetime

# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
#date_str = today_str
date_str = "05_27_2025"

input_path = f"Output_Twitter_{date_str}/top10_tweets_brief_{date_str}.json"
output_path = f"Output_Twitter_{date_str}/top10_tweets_clean_{date_str}.json"

# Load tweets
with open(input_path, "r", encoding="utf-8") as f:
    tweets = json.load(f)

top_10 = tweets[:10]

# Define phrases to remove
noise_terms = [
    r"\bJUST IN\b", r"\bBREAKING\b", r"\bUPDATE\b", r"\bBULLISH\b",
    r"\bALERT\b", r"\bHOT\b", r"\bNEW\b", r"\bLATEST\b", r"\bLIVE\b"
]

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+", "", text)  # Remove URLs
    text = re.sub(r'[^\w\s.,!?\'\"@:/%-]', '', text)  # Remove emojis
    for term in noise_terms:
        text = re.sub(term, '', text, flags=re.IGNORECASE)
    return text.strip().lstrip(":").strip()  # <-- remove leading colon and trim

# Clean and save top 10
cleaned_tweets = []
for tweet in tweets[:10]:
    cleaned_tweet = {
        #"title": tweet.get("title", ""),
        "post": clean_text(tweet.get("post", "")),
        "url": tweet.get("url", "")
    }
    cleaned_tweets.append(cleaned_tweet)

# Save to new JSON file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_tweets, f, indent=2, ensure_ascii=False)

print(f"Cleaned tweets saved to: {output_path}")