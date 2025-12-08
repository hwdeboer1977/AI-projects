import json
import psycopg2
from datetime import datetime
import os
from glob import glob

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="agent_db",
    user="postgres",
    password="Kwekebos230!",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Loop through all matching newsletter JSON files
json_files = sorted(glob("newsletter_combined_*.json"))

for file_path in json_files:
    print(f"\n📥 Processing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    date = datetime.strptime(data["date"], "%m_%d_%Y").date()

    # Build summary from market section
    market = data.get("sections", {}).get("market_colour", {})
    summary = market.get("text", "") + " " + market.get("etf_summary", "")

    # Insert or update newsletter
    cur.execute("""
        INSERT INTO newsletters (date, markdown_path, summary)
        VALUES (%s, %s, %s)
        ON CONFLICT (date) DO UPDATE SET
            markdown_path = EXCLUDED.markdown_path,
            summary = EXCLUDED.summary
        RETURNING id;
    """, (
        date,
        file_path,
        summary
    ))

    result = cur.fetchone()
    if result:
        newsletter_id = result[0]
        print(f"✅ Newsletter for {date} inserted or updated")

        # Optional: delete old articles linked to this newsletter
        cur.execute("DELETE FROM articles WHERE newsletter_id = %s;", (newsletter_id,))

        # Insert articles
        articles = data.get("sections", {}).get("top_articles", [])
        for article in articles:
            article_url = article["url"]
            article_summary = " ".join(article["summary"])

            cur.execute("""
                INSERT INTO articles (newsletter_id, url, summary, published_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """, (
                newsletter_id,
                article_url,
                article_summary,
                date
            ))

        print(f"📝 Inserted {len(articles)} articles for {date}")

    else:
        print(f"⚠️ Newsletter for {date} already exists and was not updated.")

conn.commit()
cur.close()
conn.close()
