from markdown import markdown
from datetime import datetime
import os

# Settings
today_str = datetime.now().strftime("%m_%d_%Y")
date_str = today_str
#date_str = "05_28_2025"

md_input = f"newsletter_{date_str}.md"
html_output = f"newsletter_{date_str}.html"

# Read Markdown content
with open(md_input, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert to HTML
html_content = markdown(md_content, output_format='html5')

# Wrap with basic HTML structure and inline styling
full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Crypto Newsletter – {date_str.replace("_", "/")}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            padding: 2rem;
            background-color: #f9f9f9;
            color: #222;
        }}
        h1, h2, h3 {{
            color: #111;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        img {{
            max-width: 500px;
            height: auto;
            margin-top: 1rem;
        }}
        logo {{
            float: left;
            margin-right: 20px;
            margin-bottom: 10px;
            max-width: 100px;
            height: auto;
        }}
        ul {{
            padding-left: 1.2rem;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Save to HTML file
with open(html_output, "w", encoding="utf-8") as f:
    f.write(full_html)

html_output
