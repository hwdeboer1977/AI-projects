import requests, json, os, datetime
from dotenv import load_dotenv
from credit_logger import get_current_credits, log_credits

# Get credits API before running script
credits_before = get_current_credits()


# === Config & Setup ===
load_dotenv()
API_KEY = os.getenv("TWITTER_IO_API")
if not API_KEY:
    raise ValueError("Missing TWITTER_IO_API in .env")

headers = {"x-api-key": API_KEY}
url = "https://api.twitterapi.io/twitter/user/last_tweets"

usernames = [
    "tier10k", 
    "WuBlockchain", "glassnode",
    "santimentfeed", "WatcherGuru", "CryptoQuant",
    "lookonchain", "DefiLlama"
]

# Prepare output folder
today_str = datetime.datetime.utcnow().strftime("%m_%d_%Y")
output_dir = f"Output_Twitter_{today_str}"
os.makedirs(output_dir, exist_ok=True)

# Define 24h cutoff
cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=1)

# === Main Loop ===
if __name__ == "__main__":
    for username in usernames:
        print(f"\n📡 Fetching tweets for: {username}")
        try:
            # Fetch tweets (up to 20)
            resp = requests.get(
                url, headers=headers, params={"userName": username, "count": 20}
            )
            resp.raise_for_status()
            tweets = resp.json().get("data", {}).get("tweets", [])

            results = []
            for t in tweets:
                # Filter by date
                dt = datetime.datetime.strptime(t["createdAt"], "%a %b %d %H:%M:%S %z %Y")
                dt_utc = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
                if dt_utc < cutoff:
                    continue

                # Extract only external article link
                expanded = None
                for u in t.get("entities", {}).get("urls", []):
                    exp = u.get("expanded_url", "")
                    if exp and not any(dom in exp for dom in ("twitter.com", "x.com")):
                        expanded = exp
                        break
                if not expanded:
                    continue

                # Build minimal record
                results.append({
                    "id": t["id"],
                    "text": t["text"],
                    "createdAt": t["createdAt"],
                    "url": t["url"],
                    "article_link": expanded,
                    "likeCount": t.get("likeCount", 0),
                    "retweetCount": t.get("retweetCount", 0),
                    "viewCount": t.get("viewCount", 0)
                })

            print(f"✅ Found {len(results)} tweets with links in past 24h for @{username}")

            # Write to JSON
            out_file = os.path.join(output_dir, f"{username}_links_{today_str}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved {len(results)} tweets to {out_file}")

        except Exception as e:
            print(f"❌ Failed to fetch for {username}: {e}")


# Get credits API after running script
credits_after = get_current_credits()
log_credits(credits_before, credits_after)
