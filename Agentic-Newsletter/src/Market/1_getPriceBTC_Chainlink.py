from web3 import Web3
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Note: Chainlink does not guarantee a round every minute
# It depends on volatility etc. So a round can even takes 10 minutes (if volatility is low)

load_dotenv()  # Loads the variables from .env
alchemy_key = os.getenv("ALCHEMY_API_KEY")
alchemy_url = f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}"

w3 = Web3(Web3.HTTPProvider(alchemy_url))

# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
date_str = today_str
#date_str = "05_22_2025"

# File path
output_dir = f"Output_Market_{date_str}"
os.makedirs(output_dir, exist_ok=True)
json_output_path = f"{output_dir}/market_colour_{date_str}.json"

feeds_raw = {
    "BTC/USDC": "0x6ce185860a4963106506c203335a2910413708e9",
    "ETH/USDC": "0x639fe6ab55c921f74e7fac1ee960c0b6293ba612"
}
feeds = {label: w3.to_checksum_address(addr) for label, addr in feeds_raw.items()}

aggregator_abi = [
    {
        "name": "latestRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function",
        "inputs": []
    },
    {
        "name": "getRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function",
        "inputs": [{"name": "roundId", "type": "uint80"}]
    }
]

# Helper function
def format_market_colour(btc_price, btc_24h, btc_mon, eth_price, eth_24h, eth_mon):
    def describe_asset(name, price, chg_24h, chg_mon):
        direction_24h = "up" if chg_24h >= 0 else "down"
        direction_mon = "higher" if chg_mon >= 0 else "lower"
        return (
            f"{name} is trading at ${price:,.2f}, "
            f"{direction_24h} {abs(chg_24h):.2f}% over the past 24 hours and "
            f"{abs(chg_mon):.2f}% {direction_mon} since Monday morning"
        )

    btc_sentence = describe_asset("Bitcoin", btc_price, btc_24h, btc_mon)
    eth_sentence = describe_asset("Ethereum", eth_price, eth_24h, eth_mon).replace("is", "showing a", 1)
    return f"{btc_sentence}. Meanwhile, {eth_sentence}."


# 🔎 Find closest round + return price + timestamp
def find_price_at_time(contract, target_time, latest_round):
    ts_target = int(target_time.timestamp())
    low = latest_round - 1200
    high = latest_round
    closest = None

    while low <= high:
        mid = (low + high) // 2
        data = contract.functions.getRoundData(mid).call()
        ts = data[3]

        #if abs(ts - ts_target) <= 300:
        if abs(ts - ts_target) <= 60:  # 1 minute
            return data[1] / 1e8, datetime.utcfromtimestamp(ts)
        elif ts > ts_target:
            high = mid - 1
        else:
            low = mid + 1

        # keep last valid candidate
        closest = (data[1] / 1e8, datetime.utcfromtimestamp(ts))
    return closest if closest else (None, None)

def fetch_price_changes(contract):
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    monday = now - timedelta(days=now.weekday())
    monday_6am = datetime(monday.year, monday.month, monday.day, 6, 0)

    latest = contract.functions.latestRoundData().call()
    latest_round = latest[0]
    current_price = latest[1] / 1e8

    price_yesterday, ts_yesterday = find_price_at_time(contract, yesterday, latest_round)
    price_monday, ts_monday = find_price_at_time(contract, monday_6am, latest_round)

    chg_24h = ((current_price - price_yesterday) / price_yesterday * 100) if price_yesterday else None
    chg_monday = ((current_price - price_monday) / price_monday * 100) if price_monday else None

    return current_price, chg_24h, chg_monday, ts_yesterday, ts_monday

# Collect results
btc_price = eth_price = btc_24h = eth_24h = btc_mon = eth_mon = None

print("📊 Chainlink Prices + Changes (Arbitrum)\n")
for label, address in feeds.items():
    contract = w3.eth.contract(address=address, abi=aggregator_abi)
    price, chg_24h, chg_monday, ts_24h, ts_mon = fetch_price_changes(contract)

    print(f"{label}: ${price:,.2f}")
    print(f"  24h change:      {chg_24h:+.2f}% @ {ts_24h} UTC" if chg_24h else "  24h change:      N/A")
    print(f"  Since Monday 6h: {chg_monday:+.2f}% @ {ts_mon} UTC" if chg_monday else "  Since Monday 6h: N/A")
    print("-" * 60)

    # Store values for sentence
    if "BTC" in label:
        btc_price, btc_24h, btc_mon = price, chg_24h, chg_monday
    elif "ETH" in label:
        eth_price, eth_24h, eth_mon = price, chg_24h, chg_monday

# Save JSON if complete
if all(v is not None for v in [btc_price, btc_24h, btc_mon, eth_price, eth_24h, eth_mon]):
    paragraph = format_market_colour(btc_price, btc_24h, btc_mon, eth_price, eth_24h, eth_mon)

    json_data = {
        "date": date_str,
        "btc_price": btc_price,
        "btc_change_24h": btc_24h,
        "btc_change_since_monday": btc_mon,
        "eth_price": eth_price,
        "eth_change_24h": eth_24h,
        "eth_change_since_monday": eth_mon,
        "paragraph": paragraph
    }

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    print(f"✅ JSON saved to: {json_output_path}")
else:
    print("❌ Incomplete data — could not generate JSON.")