import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import inspect

# Load environment variables
load_dotenv()

API_KEY = os.getenv("TWITTER_IO_API")
print(API_KEY)


headers = {"X-API-Key": API_KEY}



# === Function to get current credits ===
def get_current_credits():
    url = "https://api.twitterapi.io/oapi/my/info"
    try:
        response = requests.get(url, headers=headers)
        print("⚙️ Raw response:", response.text)  # debug line
        data = response.json()
        credits = int(data.get("recharge_credits", 0))
        print("🔢 Credits fetched:", credits)  # debug line
        return credits
    except Exception as e:
        print(f"⚠️ Failed to fetch credits: {e}")
        return None


# === Function to log to file ===
def log_credits(credits_before, credits_after, filename_prefix="credits_used"):
    if credits_before is None or credits_after is None:
        print("⚠️ Missing credit values, skipping log.")
        return

    used = credits_before - credits_after
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    date_str = now.strftime("%Y_%m_%d")

    # Get parent script name
    caller_path = inspect.stack()[-1].filename
    script_name = os.path.splitext(os.path.basename(caller_path))[0]


    # Compose dynamic filename
    filename = f"{filename_prefix}_{script_name}_{date_str}.txt"

    log_line = f"{timestamp} | Used: {used} | Before: {credits_before} | After: {credits_after}\n"

    with open(filename, "a", encoding="utf-8") as f:
        f.write(log_line)

    print(f"✅ Logged credit usage: {used} credits → {filename}")

# === Example usage ===
if __name__ == "__main__":
    credits_before = get_current_credits()

    # --- Your actual TwitterAPI.io logic here ---
    # response = requests.get("https://api.twitterapi.io/oapi/...")

    credits_after = get_current_credits()
    log_credits(credits_before, credits_after)