import requests
import json
import os
from datetime import datetime

API_KEY = 'SOSO-6cc7304eee8d47b4bd36f1eda97bd43a'
BASE_URL = "https://openapi.sosovalue.com/openapi/v2/etf/currentEtfDataMetrics"

def format_etf_summary(daily_inflow, cum_inflow, aum, daily_volume):
    tone = "neutral"
    if daily_inflow > 250_000_000:
        tone = "bullish"
    elif daily_inflow < -100_000_000:
        tone = "bearish"

    if tone == "bullish":
        summary = (
            f"📊 **US Bitcoin Spot ETF Flows**\n\n"
            f"Institutional demand surged with **${daily_inflow:,.0f} in net inflows**, pushing "
            f"**cumulative flows to ${cum_inflow:,.0f}**. Total AUM climbed to **${aum:,.0f}**, while "
            f"**${daily_volume:,.0f} was traded across spot ETFs** yesterday."
        )
    elif tone == "bearish":
        summary = (
            f"📊 **US Bitcoin Spot ETF Flows**\n\n"
            f"US BTC spot ETFs saw net outflows of **${abs(daily_inflow):,.0f}**, even as total AUM held "
            f"steady at **${aum:,.0f}**. Cumulative inflows remain at **${cum_inflow:,.0f}**, with "
            f"**${daily_volume:,.0f} in daily trading activity**."
        )
    else:  # neutral
        summary = (
            f"📊 **US Bitcoin Spot ETF Flows**\n\n"
            f"Spot ETFs recorded **${daily_inflow:,.0f} in daily net inflows**, boosting "
            f"**cumulative flows to ${cum_inflow:,.0f}**. Total AUM stands at **${aum:,.0f}**, with "
            f"**${daily_volume:,.0f} traded in the past 24 hours**."
        )
    return summary


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

    # Extract top-level metrics
    aum = float(metrics['totalNetAssets']['value'])
    daily_inflow = float(metrics['dailyNetInflow']['value'])
    cum_inflow = float(metrics['cumNetInflow']['value'])
    daily_volume = float(metrics['dailyTotalValueTraded']['value'])

    # 📝 Format and print summary paragraph
    summary = format_etf_summary(daily_inflow, cum_inflow, aum, daily_volume)
    print("\n" + summary + "\n")

    # 💾 Save to markdown
    today = datetime.utcnow().strftime("%m_%d_%Y")
    md_file = f"etf_flows_{today}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(summary + "\n")
    print(f"✅ Saved ETF summary to {md_file}")

    # 📦 Detailed ETF Breakdown
    print("\n📦 ETF Breakdown:\n")
    for etf in metrics["list"]:
        print(f"{etf['ticker']} ({etf['institute']})")
        print(f"  AUM: ${float(etf['netAssets']['value']):,.2f}")
        print(f"  Daily Volume: ${float(etf['dailyValueTraded']['value']):,.2f}")
        print(f"  Cumulative Flow: ${float(etf['cumNetInflow']['value']):,.2f}")
        print(f"  Fee: {float(etf['fee']['value']) * 100:.2f}%")
        print(f"  Premium/Discount: {float(etf['discountPremiumRate']['value']) * 100:.2f}%")


# 🟠 Run BTC ETF Summary
fetch_etf_metrics("us-btc-spot")
