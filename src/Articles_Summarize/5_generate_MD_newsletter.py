import json
from datetime import datetime

# Load today's article list# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
date_str = today_str
#date_str = "05_22_2025"

input_path = f"Output_{date_str}/top_10_unique_articles_{date_str}.json"
output_path = f"Output_{date_str}/newsletter_{date_str}.md"

with open(input_path, "r", encoding="utf-8") as f:
    articles = json.load(f)


# Build Markdown
lines = [
    "```{=latex}",
    "\\begin{flushleft}",
    "  \\includegraphics[width=100px]{src/Summarize/logo.png}",
    "\\end{flushleft}",
    "```",
    "",
    f"# Daily Crypto Brief – {date_str.replace('_', '/')}",
    "Here are the top 10 trending crypto stories based on Twitter engagement.\n"
]



for i, article in enumerate(articles, 1):
    title = article["title"]
    #source = article["source"]
    url = article["url"]
    #retweets = article["twitter_engagement"].get("retweets", 0)
    summary = article.get("summary", [])

    #lines.append("---")
    lines.append(f"## {i}. {title}")
    #lines.append(f"**Source:** {source}  ")
    #lines.append(f"**Retweets:** {retweets}  ")
    lines.append(f" [Read Article]({url})\n")

    if summary:
        lines.append("**Summary:**")
        lines.append("")  # Blank line before bullet points
        for bullet in summary:
            lines.append(f"- {bullet}")
    lines.append("")

# Save as Markdown
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Saved newsletter to {output_path}")
