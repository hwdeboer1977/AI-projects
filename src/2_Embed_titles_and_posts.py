from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import os
import json

# Embedding both title + post gives a richer representation of the article’s meaning.

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# File paths
input_path = "/home/lupo1977/ai-agent-env/output_22_5_2025/aggregated_title_post_05_22_2025.json"
output_path = "/home/lupo1977/ai-agent-env/output_22_5_2025/embedded_titles_05_22_2025.json"

# Load aggregated articles
with open(input_path, "r", encoding="utf-8") as f:
    articles = json.load(f)

# Create embeddings from title + post
for article in articles:
    title = article.get("title", "")
    post = article.get("post", "")
    full_text = f"{title} {post}".strip()
    
    try:
        response = client.embeddings.create(
            input=[full_text],
            model="text-embedding-3-small"
        )
        article["embedding"] = response.data[0].embedding
    except Exception as e:
        print(f"❌ Error embedding: {title[:60]}... → {e}")
        article["embedding"] = []

# Save result
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"Embedded {len(articles)} titles + posts → {output_path}")



# with open("/home/lupo1977/ai-agent-env/output_22_5_2025/Coindesk_articles_24h_05_22_2025.json", "r", encoding="utf-8") as f:
#     coindesk_articles = json.load(f)

# titles = [article["title"] for article in coindesk_articles]


# embeddings = []
# for title in titles:
#     response = client.embeddings.create(input=[title], model="text-embedding-3-small")
#     embeddings.append(response.data[0].embedding)


# # # Sample posts
# # a = "Blackstone buys $1M worth of Bitcoin ETF in first crypto bet"
# # b = "Blackstone enters crypto space with $1M in Bitcoin ETF"

# # # Get embeddings
# # # model="text-embedding-3-small" is lightweight model that turns text into numbers
# # # emb_a and emb_b are then vectors with numbers which we can compare mathematically
# # emb_a = client.embeddings.create(input=[a], model="text-embedding-3-small").data[0].embedding
# # emb_b = client.embeddings.create(input=[b], model="text-embedding-3-small").data[0].embedding

# # # Cosine similarity: one of the most popular ways to compare two text embeddings (vectors)
# # # np.dot(emb_a, emb_b) = Dot product → measures alignment between two vectors
# # # np.linalg.norm(emb_a) = length of vector a (normalized!)
# # # np.linalg.norm(emb_b) = length of vector b (normalized!)
# # cos_sim = np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b))

# # print("Similarity:", cos_sim)
