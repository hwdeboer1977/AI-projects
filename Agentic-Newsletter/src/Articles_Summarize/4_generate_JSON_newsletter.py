import json
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import openai
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
date_str = today_str
#date_str = "06_17_2025"

file_path = f"Output_{date_str}/summary_with_twitter_{date_str}.json"
output_path = f"Output_{date_str}/top_10_unique_articles_{date_str}.json"

# A. Define blacklist keywords
BLACKLIST_KEYWORDS = [
    "dead", "death", "dies", "kidnapped", "murder", "missing", "stabbed", "Xbox", "Console",
    "arrested", "jailed", "technical analysis", "RSI", "MACD", "bollinger", "indicator"
]

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# A. Fast keyword filter
def is_blacklisted(article):
    summary_text = " ".join(article.get("summary", []))  # join list into string
    combined = (article.get("title", "") + " " + summary_text).lower()
    return any(keyword in combined for keyword in BLACKLIST_KEYWORDS)

# B. GPT relevance filter
def is_relevant_article(article):
    title = article.get("title", "")
    summary = " ".join(article.get("summary", []))  # Join summary list into a string

    prompt = f"""Title: {title}
Summary: {summary}

Is this article relevant to macroeconomic, institutional, regulatory, or DeFi-related developments in the crypto market? Only answer "Yes" or "No".""" 

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    reply = response.choices[0].message.content.strip().lower()
    return reply.startswith("yes")


# Load articles
with open(file_path, "r", encoding="utf-8") as f:
    articles = json.load(f)

# Valid + clean articles
valid = []
for a in articles:
    if (
        "twitter_engagement" not in a
        or "retweets" not in a["twitter_engagement"]
        or not a.get("title")
    ):
        continue
    if is_blacklisted(a):
        continue
    if not is_relevant_article(a):
        continue
    valid.append(a)

print(f"After filtering, {len(valid)} valid articles remain.")

# === SORT + EMBEDDINGS ===
sorted_articles = sorted(valid, key=lambda a: a["twitter_engagement"]["retweets"], reverse=True)

def embed(texts):
    embeddings = []
    for i in range(0, len(texts), 10):
        batch = texts[i:i+10]
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch
        )
        embeddings.extend([np.array(e.embedding) for e in response.data])
    return embeddings

texts = [f"{a['title']} — {' '.join(a['summary'])}" for a in sorted_articles]
embeddings = embed(texts)

# === DIVERSIFY BASED ON COSINE SIMILARITY ===
selected = []
selected_vecs = []
selected_indices = []

for idx, article in enumerate(sorted_articles):
    if len(selected) >= 20:
        break
    emb = embeddings[idx].reshape(1, -1)
    if not selected_vecs:
        selected.append(article)
        selected_vecs.append(emb)
        selected_indices.append(idx)
        continue
    sim = cosine_similarity(emb, np.vstack(selected_vecs))
    if np.max(sim) < 0.40:
        selected.append(article)
        selected_vecs.append(emb)
        selected_indices.append(idx)

# === OPTIONAL: Similarity Scores ===
selected_embeddings = np.vstack([embeddings[i] for i in selected_indices])
for i, article in enumerate(selected):
    article["similarity_scores"] = []
    for j, other_article in enumerate(selected):
        if i == j:
            continue
        sim = cosine_similarity(
            selected_embeddings[i].reshape(1, -1),
            selected_embeddings[j].reshape(1, -1)
        )[0][0]
        article["similarity_scores"].append({
            "to": other_article["title"],
            "similarity": round(float(sim), 3)
        })

# === SAVE OUTPUT ===
cleaned_output = [
    {
        "title": article["title"],
        "url": article.get("url", ""),
        "summary": article.get("summary", [])
    }
    for article in selected
]

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_output, f, indent=2)

print(f"✅ Saved {len(cleaned_output)} top unique articles to {output_path}")
