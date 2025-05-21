# Twitter Tweet Scraper (past 24 hours)
# Method: Twitter API v2 + Bearer token authentication
# - Fetches recent tweets from a list of Twitter/X accounts
# - Filters tweets within the past 24 hours
# - Extracts tweet URL, full text, views, reposts, and timestamp
# - Requires a valid BEARER_TOKEN in .env file
# - Saves results to JSON files, one per account

import requests
import datetime
import json
from dotenv import load_dotenv
import os

# 1. List of Twitter usernames to fetch
usernames = [
     "tier10k",
     "WuBlockchain",
     "glassnode",
     "santimentfeed",
     "WatcherGuru",
     "CryptoQuant",
     "lookonchain",
     "DefiLlama"
]

# 2. Load API key from .env
load_dotenv()
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
if not BEARER_TOKEN:
    raise ValueError("TWITTER_BEARER_TOKEN not found in .env file")

# 3. Setup 24h time window
now = datetime.datetime.utcnow().replace(microsecond=0)
start_time = (now - datetime.timedelta(days=1)).isoformat() + "Z"

# Set up headers for Twitter API authentication
def create_headers(token):
    return {"Authorization": f"Bearer {token}"}

# Convert username to user ID (required by Twitter API v2)
def get_user_id(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    response = requests.get(url, headers=create_headers(BEARER_TOKEN))
    response.raise_for_status()
    return response.json()["data"]["id"]

# Fetch recent tweets by user ID (filtered to last 24h)
def get_recent_tweets(user_id, max_results=50):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics",
        "start_time": start_time
        # "exclude": "replies"  # optional
    }
    response = requests.get(url, headers=create_headers(BEARER_TOKEN), params=params)
    print(f"📡 API Status: {response.status_code} | URL: {response.url}")
    response.raise_for_status()
    return response.json().get("data", [])

# Extract relevant fields from tweet payload
def extract_fields(tweet, username):
    post = tweet["text"]
    title = " ".join(post.split()[:12]) # First 12 words for preview title
    tweet_id = tweet["id"]
    url = f"https://x.com/{username}/status/{tweet_id}"
    metrics = tweet.get("public_metrics", {})
    
    return {
        "title": title,
        "post": post,
        "url": url,
        "views": metrics.get("impression_count"),
        "reposts": metrics.get("retweet_count"),
        "created_at": tweet["created_at"]
    }

# Main script: loops through all usernames
if __name__ == "__main__":
    for username in usernames:
        print(f"\n📡 Fetching tweets for: {username}")
        try:
            user_id = get_user_id(username)
            tweets = get_recent_tweets(user_id)
            results = [extract_fields(tweet, username) for tweet in tweets]

             # Console preview
            for i, r in enumerate(results, 1):
                print(f"[{i}] {r['title']}")
                print(f" {r['post'][:80]}...")
                print(f" Reposts: {r['reposts']} | 📈 Views: {r['views']}")
                print(f" {r['created_at']} | 🔗 {r['url']}")
                print("-" * 60)

            today_str = datetime.datetime.now().strftime("%m_%d_%Y")
            out_file = f"Twitter_{username}_24h_{today_str}.json"

             # Save to JSON file
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"\n Saved {len(results)} tweets to {out_file}")

        except Exception as e:
            print(f"❌ Failed to fetch tweets for {username}: {e}")
