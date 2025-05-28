import os
import json
from datetime import datetime

# === Settings ===
today_str = datetime.now().strftime("%m_%d_%Y")
date_str = today_str  # or hardcode for testing
# date_str = "05_22_2025"

# === Input paths ===
market_file = f"Output_Market_{date_str}/market_colour_{date_str}.json"
etf_file = f"Output_Market_{date_str}/market_colour_ETF_{date_str}.json"
fear_greed_img_path = f"Output_Market_{date_str}/fear_and_greed_index_{date_str}.png"
output_file = f"Output_Market_{date_str}/market_colour_combined_{date_str}.json"

# === Combine Data ===
combined_data = {
    "date": date_str,
    "market_colour": {},
    "etf_flows": {},
    "fear_and_greed_image": None
}

# Section 1: Market Colour
if os.path.exists(market_file):
    with open(market_file, "r", encoding="utf-8") as f:
        combined_data["market_colour"] = json.load(f)

# Section 2: ETF Flows
if os.path.exists(etf_file):
    with open(etf_file, "r", encoding="utf-8") as f:
        combined_data["etf_flows"] = json.load(f)

# Section 3: Fear & Greed Image (as relative path or base64 if needed)
if os.path.exists(fear_greed_img_path):
    combined_data["fear_and_greed_image"] = fear_greed_img_path  # relative path
    # Optional (base64 encoded image, if needed for HTML/PDF):
    # import base64
    # with open(fear_greed_img_path, "rb") as img_f:
    #     encoded_image = base64.b64encode(img_f.read()).decode("utf-8")
    #     combined_data["fear_and_greed_image_base64"] = encoded_image

# === Save Final Combined JSON ===
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(combined_data, f, indent=2)

print(f"Combined JSON newsletter saved to: {output_file}")
