import os
import re
import time
import requests
from dotenv import load_dotenv

# === ENV SETUP ===
load_dotenv("src/.env")
NOTION_TOKEN = os.getenv("AGENTIC_NOTION_API")
PARENT_PAGE_ID = os.getenv("AGENTIC_DATABASE_API")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# === BLOCK BUILDERS ===
def make_paragraph(text):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text":[{"type":"text","text":{"content":text}}]}
    }

def make_bullet(text):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":text}}]}
    }

def make_heading(level, text):
    return {
        "object":"block",
        "type":f"heading_{level}",
        f"heading_{level}":{"rich_text":[{"type":"text","text":{"content":text}}]}
    }

def make_link_paragraph(text, url):
    return {
        "object":"block",
        "type":"paragraph",
        "paragraph":{"rich_text":[{
            "type":"text",
            "text":{"content":text,"link":{"url":url}},
            "annotations":{"bold":True}
        }]}
    }

# === IMAGE UPLOAD ===
def upload_image(path):
    name = os.path.basename(path)
    # 1) start upload
    r = requests.post(
        "https://api.notion.com/v1/file_uploads",
        headers=HEADERS,
        json={"filename":name,"content_type":"image/png"}
    )
    upload_id = r.json()["id"]
    # 2) send file bytes
    with open(path,"rb") as f:
        files={"file":(name,f,"image/png")}
        r2 = requests.post(
            f"https://api.notion.com/v1/file_uploads/{upload_id}/send",
            headers={"Authorization":f"Bearer {NOTION_TOKEN}","Notion-Version":"2022-06-28"},
            files=files
        )
        r2.raise_for_status()
    # 3) wait until done
    for _ in range(5):
        status = requests.get(f"https://api.notion.com/v1/file_uploads/{upload_id}",headers=HEADERS).json()["status"]
        if status=="uploaded":
            return upload_id
        time.sleep(1)
    raise RuntimeError("Upload timed out")

def parse_markdown_with_image(md_path, upload_id):
    blocks = []
    lines = open(md_path, "r", encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i].strip()

        # 1) Skip raw HTML <img> tags
        if raw.startswith("<img") and raw.endswith("/>"):
            i += 1
            continue

        # 2) Skip the Markdown “# Daily Crypto Market Pulse” and “Date: …” lines
        if raw.startswith("# Daily Crypto Market Pulse") or raw.startswith("**Date:"):
            i += 1
            continue

        # 3) Market Colour → notch-2 heading
        if raw.startswith("## Market Colour"):
            blocks.append(make_heading(2, "Market Colour"))
            i += 1
            continue

        # 4) Fear & Greed → chart only (no heading text)
        if "Fear & Greed" in raw:
            blocks.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "file_upload",
                    "file_upload": {"id": upload_id}
                }
            })
            i += 1
            continue

        # 5) Top 10 News Articles → heading_2
        if raw.startswith("## 🗞️ Top 10 News Articles"):
            blocks.append(make_heading(2, "🗞️ Top 10 News Articles"))
            i += 1
            continue

        # 6) Top 10 Crypto Tweets → heading_2
        if raw.startswith("## 🐦 Top 10 Crypto Tweets"):
            blocks.append(make_heading(2, "🐦 Top 10 Crypto Tweets"))
            i += 1
            continue

        # 7) Numbered article links: ### 1. [Title](url)
        m = re.match(r"###\s*(\d+\.)\s*\[([^\]]+)\]\((https?://\S+)\)", raw)
        if m:
            num, title, url = m.groups()
            blocks.append(make_link_paragraph(f"{num} {title}", url))

            # grab following markdown bullets
            i += 1
            while i < len(lines) and lines[i].strip().startswith("- "):
                blocks.append(make_bullet(lines[i].strip()[2:].strip()))
                i += 1
            continue

        # 8) Tweet titles: ### N. Tweet text  (no link)
        m2 = re.match(r"###\s*(\d+\.)\s*(.+)", raw)
        if m2:
            num, tweet = m2.groups()
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"{num} {tweet}"},
                        #"annotations": {"bold": false}
                    }]
                }
            })
            i += 1
            continue

        # 9) Standalone markdown links, e.g. [View Tweet](https://...)
        lm = re.match(r"^\[([^\]]+)\]\((https?://\S+)\)$", raw)
        if lm:
            text, url = lm.groups()
            blocks.append(make_link_paragraph(text, url))
            i += 1
            continue

        # 10) Plain bullets
        if raw.startswith("- "):
            blocks.append(make_bullet(raw[2:].strip()))
            i += 1
            continue

        # 11) Anything else → paragraph (strip stray brackets)
        if raw:
            blocks.append(make_paragraph(raw.strip("[]")))

        i += 1

    return blocks

# === CREATE PAGE WITH CHILDREN ===
def create_newsletter_subpage(title,blocks):
    r=requests.post(
      "https://api.notion.com/v1/pages",
      headers=HEADERS,
      json={
        "parent":{"page_id":PARENT_PAGE_ID},
        "properties":{"title":[{"type":"text","text":{"content":title}}]},
        "children":blocks
      }
    )
    r.raise_for_status()
    print(f"✅ Created {title}")

# === MAIN ===
newsletters=[
  #{"date":"06_03_2025","md_path":"newsletter_06_03_2025.md","img_path":"Output_Market_06_03_2025/fear_and_greed_index_06_03_2025_small.png"},
  {"date":"06_04_2025","md_path":"newsletter_06_04_2025.md","img_path":"Output_Market_06_04_2025/fear_and_greed_index_06_04_2025_small.png"},
  {"date":"06_05_2025","md_path":"newsletter_06_05_2025.md","img_path":"Output_Market_06_05_2025/fear_and_greed_index_06_05_2025_small.png"}
]

for nl in newsletters:
    title=f"Newsletter {nl['date']}"
    print("📦",title)
    uid=upload_image(nl["img_path"])
    blks=parse_markdown_with_image(nl["md_path"],uid)
    create_newsletter_subpage(title,blks)
