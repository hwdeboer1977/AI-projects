import subprocess
import os
from datetime import datetime

# Load today's article list# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
date_str = today_str
#date_str = "06_12_2025"


md_file = f"Output_{date_str}/newsletter_{date_str}.md"
pdf_file = md_file.replace(".md", ".pdf")

# Optional Pandoc options
pandoc_args = [
    "pandoc",
    md_file,
    "-o", pdf_file,
    "--pdf-engine=pdflatex",
    #"--toc",  # optional: add table of contents
    #"--metadata", "title=Daily Crypto Brief",
    "--variable", "geometry=margin=1in",
    "--variable", "colorlinks=true",        # Enable colored links
    "--variable", "linkcolor=blue"          # Set link color to blue
]

# Run Pandoc
result = subprocess.run([
    "pandoc", md_file, "-o", pdf_file,
    "--pdf-engine=pdflatex",
    "-V", "geometry:margin=1in",
    "-V", "fontsize=12pt",  # increase font size here
    "-V", "colorlinks=true",         # enable colored links
    "-V", "linkcolor=blue",          # set link color to blue
    "-V", "header-includes=\\usepackage{graphicx}"
])

# # Run Pandoc
# result = subprocess.run(pandoc_args, capture_output=True, text=True)

if result.returncode == 0:
    print(f"PDF created: {pdf_file}")
else:
    print("Pandoc failed:")
    print(result.stderr)
