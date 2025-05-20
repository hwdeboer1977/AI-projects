import requests
import datetime
import json
from dotenv import load_dotenv
import os

# ✅ 1. Initialize your target username ONCE
username = "coindesk"
#username = "cointelegraph"
# username = "decryptmedia"
# username = "beincrypto"

# ✅ 2. Load API key from .env
load_dotenv()
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
if not BEARER_TOKEN:
    raise ValueError("TWITTER_BEARER_TOKEN not found in .env file")

# ✅ 3. Define API endpoints
USER_LOOKUP_URL = f"https://api.twitter.com/2/users/by/username/{username}"
TWEETS_URL = "https://api.twitter.com/2/users/{user_id}/tweets"

# ✅ 4. Setup 24h time window
now = datetime.datetime.utcnow().replace(microsecond=0)
start_time = (now - datetime.timedelta(days=1)).isoformat() + "Z"

def create_headers(token):
    return {"Authorization": f"Bearer {token}"}

def get_user_id(username):
    response = requests.get(USER_LOOKUP_URL, headers=create_headers(BEARER_TOKEN))
    response.raise_for_status()
    return response.json()["data"]["id"]

def get_recent_tweets(user_id, max_results=50):
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics",
        "start_time": start_time
        # "exclude": "replies"
    }
    response = requests.get(TWEETS_URL.format(user_id=user_id), headers=create_headers(BEARER_TOKEN), params=params)
    print(f"📡 API Status: {response.status_code} | URL: {response.url}")
    response.raise_for_status()
    return response.json().get("data", [])

def extract_fields(tweet, username):
    post = tweet["text"]
    title = " ".join(post.split()[:12])
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

# ✅ 5. Main script
if __name__ == "__main__":
    user_id = get_user_id(username)
    tweets = get_recent_tweets(user_id)
    results = [extract_fields(tweet, username) for tweet in tweets]

    # ✅ Print and save
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['title']}")
        print(f"📄 {r['post'][:80]}...")
        print(f"🔁 Reposts: {r['reposts']} | 📈 Views: {r['views']}")
        print(f"⏰ {r['created_at']} | 🔗 {r['url']}")
        print("-" * 60)

    out_file = f"{username}_24h.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(results)} tweets to {out_file}")
