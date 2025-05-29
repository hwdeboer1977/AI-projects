import requests
import datetime
import json
from dotenv import load_dotenv
import os
import time

# 1. Initialize your target usernames
usernames = [
    "coindesk", "cointelegraph", "decryptmedia", "beincrypto",
    "DefiantNews", "Blockworks_", "TheBlock__"
]

# 2. Load API key
load_dotenv()
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
if not BEARER_TOKEN:
    raise ValueError("TWITTER_BEARER_TOKEN not found in .env file")

# 3. Time window
now = datetime.datetime.utcnow().replace(microsecond=0)
start_time = (now - datetime.timedelta(days=1)).isoformat() + "Z"

def create_headers(token):
    return {"Authorization": f"Bearer {token}"}

# Retry wrapper for rate-limited requests
def fetch_with_retry(url, params=None, wait_time=900):
    while True:
        response = requests.get(url, headers=create_headers(BEARER_TOKEN), params=params)
        print(f"API Status: {response.status_code} | URL: {response.url}")
        if response.status_code == 429:
            print("Rate limit hit! Waiting 15 minutes...")
            time.sleep(wait_time)
            continue
        response.raise_for_status()
        return response.json()

def get_user_id(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    print(f"Getting user ID for {username}")
    data = fetch_with_retry(url)
    return data["data"]["id"]

def get_recent_tweets(user_id, max_results=50):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics",
        "start_time": start_time
    }
    data = fetch_with_retry(url, params=params)
    if "data" not in data:
        print("No tweets returned in the last 24 hours.")
        return []
    return data.get("data", [])

def extract_fields(tweet, username):
    post = tweet.get("text", "")
    title = " ".join(post.split()[:12])
    tweet_id = tweet["id"]
    url = f"https://x.com/{username}/status/{tweet_id}"
    metrics = tweet.get("public_metrics", {})
    return {
        "title": title,
        "post": post,
        "url": url,
        "views": metrics.get("impression_count", "N/A"),
        "reposts": metrics.get("retweet_count", 0),
        "created_at": tweet.get("created_at")
    }

# Main logic
if __name__ == "__main__":
    today_str = datetime.datetime.now().strftime("%m_%d_%Y")
    output_dir = f"Output_Twitter_{today_str}"
    os.makedirs(output_dir, exist_ok=True)

    for username in usernames:
        print(f"\nFetching tweets for: {username}")
        try:
            user_id = get_user_id(username)
            print(f"{username} → user_id: {user_id}")
            tweets = get_recent_tweets(user_id)

            if not tweets:
                print(f"ℹNo tweets from {username} in the last 24 hours.\n" + "-" * 60)
                continue

            results = [extract_fields(tweet, username) for tweet in tweets]

            for i, r in enumerate(results, 1):
                print(f"[{i}] {r['title']}")
                print(f" {r['post'][:80]}...")
                print(f" Reposts: {r['reposts']} | Views: {r['views']}")
                print(f" {r['created_at']} | 🔗 {r['url']}")
                print("-" * 60)

            out_file = os.path.join(output_dir, f"Twitter_{username}_24h_{today_str}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"\nSaved {len(results)} tweets to {out_file}")

        except Exception as e:
            print(f"Failed to fetch tweets for {username}: {e}")
