import requests
import os
from dotenv import load_dotenv

load_dotenv("src/.env")

NOTION_TOKEN = os.getenv("AGENTIC_NOTION_API")
PAGE_ID = os.getenv("AGENTIC_DATABASE_API")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28"
}

# Step 1: Get all child blocks of the page
url = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"
res = requests.get(url, headers=headers)
blocks = res.json().get("results", [])

# Step 2: Delete all child blocks
for block in blocks:
    block_id = block["id"]
    del_url = f"https://api.notion.com/v1/blocks/{block_id}"
    del_res = requests.delete(del_url, headers=headers)
    print(f"Deleted {block_id} — Status: {del_res.status_code}")

clear_cover = {
    "cover": None
}

response = requests.patch(
    f"https://api.notion.com/v1/pages/{PAGE_ID}",
    headers={
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    },
    json=clear_cover
)

if response.status_code != 200:
    print(f"❌ Failed to remove cover: {response.text}")
else:
    print("✅ Cover image removed.")

