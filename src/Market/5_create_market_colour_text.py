import json
from datetime import datetime
import os

# === Settings ===
today_str = datetime.now().strftime("%m_%d_%Y")
date_str = today_str  # or hardcode for testing

# Load your combined JSON
with open(f"Output_Market_{date_str}/market_colour_combined_{date_str}.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract the values from loaded JSON
market_colour_text = data.get("market_colour", {}).get("paragraph", "")
etf_flows_text = data.get("etf_flows", {}).get("summary", "")

# Save to proper JSON
output_json = {
    "date": date_str,
    "market_colour": {
        "paragraph": market_colour_text
    },
    "etf_flows": {
        "summary": etf_flows_text
    }
}

with open(f"Output_Market_{date_str}/final_market_colour_text_{date_str}.json", "w", encoding="utf-8") as out:
    json.dump(output_json, out, indent=2)

print("✅ Saved cleaned final_market_colour_text JSON")
