import json
import re
from datetime import datetime

# Settings
today_str = datetime.now().strftime("%m_%d_%Y")
input_path = f"Output_Twitter_05_22_2025/top10_tweets_brief_{today_str}.json"
output_path = f"Output_Twitter_05_22_2025/top10_tweets_clean_{today_str}.html"

# Load tweets
with open(input_path, "r", encoding="utf-8") as f:
    tweets = json.load(f)

top_10 = tweets[:10]

# Define phrases to remove
noise_terms = [
    r"\bJUST IN\b", r"\bBREAKING\b", r"\bUPDATE\b",
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


# HTML setup
html_lines = [
    "<!DOCTYPE html>",
    "<html lang='en'>",
    "<head>",
    "  <meta charset='UTF-8'>",
    "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
    f"  <title>Top 10 Trending Tweets – {today_str.replace('_', '/')}</title>",
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
    f"<h1>Top 10 Trending Tweets – {today_str.replace('_', '/')}</h1>"
]

# Add tweets
for i, tweet in enumerate(top_10, 1):
    title = clean_text(tweet.get('title', ''))
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

print(f"Saved clean HTML newsletter to {output_path}")
