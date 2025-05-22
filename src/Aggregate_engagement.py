import json

# Sample article with related tweets
article = {
    "title": "Blackstone buys $1M worth of Bitcoin ETF in first crypto bet",
    "url": "https://cointelegraph.com/news/blackstone-buys-1-million-blackrock-bitcoin-etf-ibit",
    "related_tweets": [
        {
            "public_metrics": {
                "retweet_count": 1,
                "reply_count": 0,
                "like_count": 0,
                "quote_count": 0,
                "bookmark_count": 0,
                "impression_count": 0
            }
        },
        {
            "public_metrics": {
                "retweet_count": 1,
                "reply_count": 0,
                "like_count": 1,
                "quote_count": 0,
                "bookmark_count": 0,
                "impression_count": 72
            }
        },
        {
            "public_metrics": {
                "retweet_count": 0,
                "reply_count": 0,
                "like_count": 0,
                "quote_count": 0,
                "bookmark_count": 0,
                "impression_count": 5
            }
        },
        {
            "public_metrics": {
                "retweet_count": 0,
                "reply_count": 1,
                "like_count": 0,
                "quote_count": 0,
                "bookmark_count": 0,
                "impression_count": 9
            }
        },
        {
            "public_metrics": {
                "retweet_count": 0,
                "reply_count": 0,
                "like_count": 0,
                "quote_count": 0,
                "bookmark_count": 0,
                "impression_count": 14
            }
        },
        {
            "public_metrics": {
                "retweet_count": 0,
                "reply_count": 0,
                "like_count": 0,
                "quote_count": 0,
                "bookmark_count": 0,
                "impression_count": 23
            }
        },
        {
            "public_metrics": {
                "retweet_count": 0,
                "reply_count": 0,
                "like_count": 2,
                "quote_count": 0,
                "bookmark_count": 0,
                "impression_count": 25
            }
        }
    ]
}

# Aggregating metrics
aggregated_metrics = {
    "retweets": 0,
    "replies": 0,
    "likes": 0,
    "quotes": 0,
    "bookmarks": 0,
    "impressions": 0
}

for tweet in article["related_tweets"]:
    metrics = tweet["public_metrics"]
    aggregated_metrics["retweets"] += metrics["retweet_count"]
    aggregated_metrics["replies"] += metrics["reply_count"]
    aggregated_metrics["likes"] += metrics["like_count"]
    aggregated_metrics["quotes"] += metrics["quote_count"]
    aggregated_metrics["bookmarks"] += metrics["bookmark_count"]
    aggregated_metrics["impressions"] += metrics["impression_count"]

# Print or store results
print(f"\n Engagement for: {article['title']}")
for key, value in aggregated_metrics.items():
    print(f"{key.capitalize()}: {value}")
