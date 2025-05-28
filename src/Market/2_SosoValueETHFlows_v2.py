import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()  # Loads the variables from .env


API_KEY =  os.getenv("SOSOVALUE_API_KEY_HW")
BASE_URL = "https://openapi.sosovalue.com/openapi/v2/etf/currentEtfDataMetrics"

# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
date_str = today_str
#date_str = "05_22_2025"

# File path
output_dir = f"Output_Market_{date_str}"
os.makedirs(output_dir, exist_ok=True)
json_output_path = f"{output_dir}/market_colour_ETF_{date_str}.json"


def format_etf_summary(daily_inflow, cum_inflow, aum, daily_volume):
    tone = "neutral"
    if daily_inflow > 250_000_000:
        tone = "bullish"
    elif daily_inflow < -100_000_000:
        tone = "bearish"

    if tone == "bullish":
        summary = (
            f"Institutional demand surged with ${daily_inflow:,.0f} in net inflows, pushing "
            f"cumulative flows to ${cum_inflow:,.0f}. AUM climbed to ${aum:,.0f}, with "
            f"${daily_volume:,.0f} traded across spot ETFs yesterday."
        )
    elif tone == "bearish":
        summary = (
            f"US BTC spot ETFs saw net outflows of ${abs(daily_inflow):,.0f}. AUM held steady at ${aum:,.0f}, "
            f"cumulative inflows remain at ${cum_inflow:,.0f}, and ${daily_volume:,.0f} in trading volume."
        )
    else:  # neutral
        summary = (
            f"Spot ETFs recorded ${daily_inflow:,.0f} in net inflows, raising cumulative flows to ${cum_inflow:,.0f}. "
            f"AUM is now ${aum:,.0f}, with ${daily_volume:,.0f} traded in the last 24 hours."
        )
    return summary, tone


def fetch_etf_metrics(etf_type: str):
    headers = {
        "Content-Type": "application/json",
        "x-soso-api-key": API_KEY
    }
    body = {
        "type": etf_type
    }

    response = requests.post(BASE_URL, headers=headers, json=body)

    if response.status_code != 200:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    if data["code"] != 0:
        print(f"API Error: {data.get('msg', 'Unknown error')}")
        return

    metrics = data["data"]

    # Extract summary metrics
    aum = float(metrics['totalNetAssets']['value'])
    daily_inflow = float(metrics['dailyNetInflow']['value'])
    cum_inflow = float(metrics['cumNetInflow']['value'])
    daily_volume = float(metrics['dailyTotalValueTraded']['value'])

    summary, tone = format_etf_summary(daily_inflow, cum_inflow, aum, daily_volume)
    print("\n🧾 ETF Summary:\n" + summary)

    # Format detailed ETF data
    etf_list = []
    for etf in metrics["list"]:
        etf_list.append({
            "ticker": etf["ticker"],
            "institute": etf["institute"],
            "aum": float(etf["netAssets"]["value"]),
            "daily_volume": float(etf["dailyValueTraded"]["value"]),
            "cumulative_flow": float(etf["cumNetInflow"]["value"]),
            "fee": float(etf["fee"]["value"]),
            "premium_discount": float(etf["discountPremiumRate"]["value"])
        })

    

    json_data = {
        "date": date_str,
        "etf_type": etf_type,
        "summary": summary,
        "tone": tone,
        "daily_inflow": daily_inflow,
        "cumulative_inflow": cum_inflow,
        "aum": aum,
        "daily_volume": daily_volume,
        "etfs": etf_list
    }

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    print(f"\nSaved ETF summary and breakdown to {json_output_path}")


#  Run BTC ETF Summary
fetch_etf_metrics("us-btc-spot")
