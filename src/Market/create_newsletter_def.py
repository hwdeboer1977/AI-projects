import json
from datetime import datetime

# === Paths ===
today_str = datetime.utcnow().strftime("%m_%d_%Y")
news_md_path = f"Output_{today_str}/newsletter_{today_str}.md"
tweets_json_path = f"Output_Twitter_{today_str}/top10_tweets_brief_{today_str}.json"
market_md_path = f"market_colour_{today_str}.md"
output_path = f"final_newsletter_{today_str}.md"

# === Combine ===
with open(output_path, "w", encoding="utf-8") as out:
    out.write(f"# 📰 Daily Market Newsletter — {today_str.replace('_', '-')}\n\n")

    # 📊 Section 1: Market Summary
    if market_md_path:
        out.write("## 📊 Market Overview\n\n")
        with open(market_md_path, "r", encoding="utf-8") as f:
            out.write(f.read().strip() + "\n\n")


    # 📰 Section 2: News Article Summaries
    if news_md_path:
        out.write("## 🗞️ News Highlights\n\n")
        with open(news_md_path, "r", encoding="utf-8") as f:
            out.write(f.read().strip() + "\n\n")

    # 🐦 Section 3: Top Tweets
    if tweets_json_path:
        out.write("## 🐦 Top 10 Crypto Tweets (24h)\n\n")
        with open(tweets_json_path, "r", encoding="utf-8") as f:
            tweets = json.load(f)
            for i, tweet in enumerate(tweets, 1):
                out.write(f"**{i}.** {tweet['post']}\n")
                out.write(f"🔗 [View Tweet]({tweet['url']})\n\n")
                out.write("---\n\n")


print(f"✅ Final newsletter saved to: {output_path}")


#pandoc final_newsletter_05_27_2025.md -o final_newsletter_05_27_2025.html
