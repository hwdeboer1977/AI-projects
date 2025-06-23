import requests, json, os, datetime
from dotenv import load_dotenv
from credit_logger import get_current_credits, log_credits

# Get credits API before running script
credits_before = get_current_credits()


# ✅ 1. Configuration
load_dotenv()
API_KEY = os.getenv("TWITTER_IO_API")
if not API_KEY:
    raise ValueError("Missing TWITTER_IO_API in .env")

headers = {"x-api-key": API_KEY}
url = "https://api.twitterapi.io/twitter/user/last_tweets"

# Target usernames
usernames = [
    "coindesk", 
    "cointelegraph", "decryptmedia", "beincrypto",
    "DefiantNews", "Blockworks_", "TheBlock__"
]

# 24‑hour cutoff
cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=1)

# Create output folder
today_str = datetime.datetime.utcnow().strftime("%m_%d_%Y")
output_dir = f"Output_Twitter_{today_str}"
os.makedirs(output_dir, exist_ok=True)

# ✅ 2. Main loop
if __name__ == "__main__":
    for username in usernames:
        print(f"\n📡 Fetching tweets for: {username}")
        try:
            # Fetch latest tweets
            params = {"userName": username, "count": 20}
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            tweets = resp.json().get("data", {}).get("tweets", [])
            results = []

            # Filter tweets
            for t in tweets:
                created = datetime.datetime.strptime(
                    t["createdAt"], "%a %b %d %H:%M:%S %z %Y"
                ).astimezone(datetime.timezone.utc).replace(tzinfo=None)
                if created < cutoff:
                    continue

                # Find external article link
                exp_link = None
                for u in t.get("entities", {}).get("urls", []):
                    url_exp = u.get("expanded_url")
                    if url_exp and "twitter.com" not in url_exp and "x.com" not in url_exp:
                        exp_link = url_exp
                        break
                if not exp_link:
                    continue

                results.append({
                    "id": t["id"],
                    "text": t["text"],
                    "createdAt": t["createdAt"],
                    "url": t["url"],
                    "article_link": exp_link,
                    "likeCount": t.get("likeCount", 0),
                    "retweetCount": t.get("retweetCount", 0),
                    "viewCount": t.get("viewCount", 0)
                })

            print(f"✅ @{username}: {len(results)} tweets with article links in past 24h")

            # Save per‑user JSON
            out_path = os.path.join(output_dir, f"{username}_links_{today_str}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved → {out_path}")

        except Exception as e:
            print(f"❌ Failed for {username}: {e}")

# Get credits API after running script
credits_after = get_current_credits()
log_credits(credits_before, credits_after)
