import glob
import os
import json
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import openai
import re


# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)



# Settings
today_str = datetime.now().strftime("%m_%d_%Y")

# Select current date or earlier data (if you want to access earlier dates)
date_str = today_str
#date_str = "05_22_2025"

output_path = f"Output_Twitter_{date_str}/top_trending_tweets_labeled_{date_str}.json"

# Clean text helper
# List of noisy intro phrases to remove
# These often appear in many tweets but don't contribute meaningfully to the content. 
# Yet they inflate the similarity score because they’re repeated across unrelated tweets
# Clean text helper
noise_terms = [
    r"\bJUST IN\b", r"\bBREAKING\b", r"\bUPDATE\b",
    r"\bALERT\b", r"\bHOT\b", r"\bNEW\b", r"\bLIVE\b"
]


def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+", "", text)
    for term in noise_terms:
        text = re.sub(term, "", text, flags=re.IGNORECASE)
    return text.strip()

# Aggregate tweets
all_tweets = []
for path in glob.glob(f"Output_Twitter_{date_str}/*.json"):
    with open(path, "r", encoding="utf-8") as f:
        tweets = json.load(f)
        all_tweets.extend(tweets)

# Score and sort
def engagement_score(tweet):
    return tweet.get("retweetCount", 0) * 10 + tweet.get("viewCount", 0)

for tweet in all_tweets:
    tweet["engagement_score"] = engagement_score(tweet)

top_tweets = sorted(all_tweets, key=lambda x: x["engagement_score"], reverse=True)[:50]

# Clean and filter text
valid_tweets = []
cleaned_texts = []

for tweet in top_tweets:
    text = clean_text(tweet.get("text", ""))
    if text:
        cleaned_texts.append(text)
        valid_tweets.append(tweet)

# Embed
# Select top 50 (or any N)
# Note that we can compare similarity between posts using embedding
# However, it takes 50 * 50 comparisons then? Not really
# The matrix is symmetric and we only need the upper triangle (exclude the diagonal)
# So n(n-1) / 2 = 50 * 49 / 2 = 1225 comparisons
embeddings = []
for i in range(0, len(cleaned_texts), 10):
    batch = cleaned_texts[i:i+10]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=batch
    )
    embeddings.extend([np.array(e.embedding) for e in response.data])

# Compute similarity
similarity_matrix = cosine_similarity(embeddings)

# Annotate with top 3 similar tweets
for i, tweet in enumerate(valid_tweets):
    similarities = []
    for j, score in enumerate(similarity_matrix[i]):
        if i != j:
            similarities.append((j, float(score)))
    top_similar = sorted(similarities, key=lambda x: x[1], reverse=True)[:3]
    tweet["similar_tweets"] = [
        {
            "title": valid_tweets[j].get("title", valid_tweets[j].get("text", ""))[:100],
            "url": valid_tweets[j].get("url"),
            "article_link": valid_tweets[j].get("article_link", None),
            "similarity": round(score, 3)
        }
        for j, score in top_similar
    ]

# Save results
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(valid_tweets, f, indent=2, ensure_ascii=False)

print(f"Saved labeled tweets to {output_path}")








