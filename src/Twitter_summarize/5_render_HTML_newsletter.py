import json
import re
from datetime import datetime

# Settings
today_str = datetime.now().strftime("%m_%d_%Y")
date_str = "05_27_2025"  # Or use today_str

input_path = f"Output_Twitter_{date_str}/top10_tweets_clean_{date_str}.json"
output_path = f"Output_Twitter_{date_str}/top10_tweets_clean_{date_str}.html"

# Load tweets
with open(input_path, "r", encoding="utf-8") as f:
    tweets = json.load(f)

top_10 = tweets[:10]

# Optional cleanup in case some raw text slipped in
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r'[^\w\s.,!?\'\"@:/%-]', '', text)
    return text.strip().lstrip(":").strip()

# HTML setup
html_lines = [
    "<!DOCTYPE html>",
    "<html lang='en'>",
    "<head>",
    "  <meta charset='UTF-8'>",
    "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
    f"  <title>Top 10 Trending Tweets – {date_str.replace('_', '/')}</title>",
    "  <style>",
    "    body { font-family: Arial, sans-serif; padding: 2rem; background: #fff; color: #111; }",
    "    h1 { font-size: 1.8em; margin-bottom: 1.5rem; }",
    "    h2 { font-size: 1.3em; margin-top: 1.8rem; }",
    "    p { margin-bottom: 0.8rem; }",
    "    a { color: #1a0dab; text-decoration: none; }",
    "    hr { margin: 2rem 0; border: none; border-top: 1px solid #ccc; }",
    "  </style>",
    "</head>",
    "<body>",
    f"<h1>Top 10 Trending Tweets – {date_str.replace('_', '/')}</h1>"
]

# Add tweets
for i, tweet in enumerate(top_10, 1):
    post = clean_text(tweet.get('post', ''))
    url = tweet['url']
    html_lines.append(f"<h2>{i}. {post}</h2>")
    html_lines.append(f"<p><a href='{url}' target='_blank'>View Tweet</a></p>")
    html_lines.append("<hr>")

html_lines.append("</body>")
html_lines.append("</html>")

# Save to HTML
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(html_lines))

print(f"Saved clean HTML newsletter to: {output_path}")
