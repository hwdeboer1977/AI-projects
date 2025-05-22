from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Define input/output
base_dir = "/home/lupo1977/ai-agent-env/output_22_5_2025"
input_files = [
    "Defiant_articles_24h_05_22_2025.json",
    "Decrypt_articles_24h_05_22_2025.json",
    "Cointelegraph_articles_24h_05_22_2025.json",
    "Coindesk_articles_24h_05_22_2025.json",
    "Blockworks_articles_24h_05_22_2025.json",
    "BeInCrypto_articles_24h_05_22_2025.json"
]

aggregated = []

# Step 1: Aggregate articles with full title + post
for file in input_files:
    full_path = os.path.join(base_dir, file)
    source = file.split("_")[0]  # Extract source name from filename
    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for article in data:
            if article.get("title"):
                combined_text = article["title"]
                if article.get("post"):
                    combined_text += " " + article["post"]
                aggregated.append({
                    "title": article["title"],
                    "post": article.get("post", ""),
                    "source": source,
                    "url": article.get("url", ""),
                    "published": article.get("published", ""),
                    "embedding_text": combined_text
                })

# Save to intermediate file
aggregated_path = os.path.join(base_dir, "aggregated_title_post_05_22_2025.json")
with open(aggregated_path, "w", encoding="utf-8") as f:
    json.dump(aggregated, f, ensure_ascii=False, indent=2)

print(f"Aggregated {len(aggregated)} articles with post → {aggregated_path}")

# Step 2: Generate embeddings
output_path = os.path.join(base_dir, "embedded_title_post_05_22_2025.json")

for article in aggregated:
    try:
        response = client.embeddings.create(
            input=[article["embedding_text"]],
            model="text-embedding-3-small"
        )
        article["embedding"] = response.data[0].embedding
        del article["embedding_text"]  # Clean up
    except Exception as e:
        print(f"❌ Embedding failed for: {article['title'][:60]} → {e}")
        article["embedding"] = []

# Save with embeddings
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(aggregated, f, ensure_ascii=False, indent=2)

print(f"Saved embedded data to {output_path}")



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
