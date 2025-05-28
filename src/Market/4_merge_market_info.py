from datetime import datetime
import os
import shutil

today_str = datetime.utcnow().strftime("%m_%d_%Y")

# File paths
etf_file = f"etf_flows_{today_str}.md"
market_file = f"market_colour_{today_str}.md"
fear_greed_img = f"fear_and_greed_index_{today_str}.png"
output_file = f"market_colour_{today_str}.md"

# Combine content
with open(output_file, "w", encoding="utf-8") as out:


    # Section 1: Market Colour
    if os.path.exists(market_file):
        with open(market_file, "r", encoding="utf-8") as f:
            out.write(f.read().strip() + "\n\n")

    # Section 2: ETF Flows
    if os.path.exists(etf_file):
        with open(etf_file, "r", encoding="utf-8") as f:
            out.write(f.read().strip() + "\n\n")

    
    # Section 3: Fear & Greed Index
    if os.path.exists(fear_greed_img):
        out.write("## Crypto Fear & Greed Index\n\n")
        out.write(f"![Fear and Greed Index](./{fear_greed_img})\n\n")



print(f"Combined newsletter saved to: {output_file}")
