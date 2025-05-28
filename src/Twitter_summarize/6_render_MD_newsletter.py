import json
from datetime import datetime

today_str = datetime.now().strftime("%m_%d_%Y")
#date_str = today_str
date_str = "05_27_2025"

input_path = f"Output_Twitter_{date_str}/top10_tweets_clean_{date_str}.json"
md_path = f"Output_Twitter_{date_str}/top10_tweets_clean_{date_str}.md"

# Load tweets
with open(input_path, "r", encoding="utf-8") as f:
    tweets = json.load(f)

top_10 = tweets[:10]

# Convert to Markdown
with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# 🐦 Top 10 Trending Tweets – {date_str.replace('_', '/')}\n\n")
    for i, tweet in enumerate(top_10, 1):
        post = tweet['post'].strip()
        url = tweet['url']
        f.write(f"## {i}. {post}\n\n")
        f.write(f"[View Tweet]({url})\n\n")
        f.write("---\n\n")

print(f"Saved markdown file to: {md_path}")
