import requests
from datetime import datetime
import os

today_str = datetime.utcnow().strftime("%m_%d_%Y")

def download_fear_greed_chart(filepath=f"Output_Market_{today_str}/fear_and_greed_index_{today_str}.png"):
    url = "https://alternative.me/crypto/fear-and-greed-index.png"
    response = requests.get(url)

    if response.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Image saved to {filepath}")
    else:
        print(f"Failed to download image (HTTP {response.status_code})")

download_fear_greed_chart()
