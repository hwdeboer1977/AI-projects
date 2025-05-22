import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict


# Load embeddings file
with open("output_22_5_2025/embedded_titles_05_22_2025.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# Extract embeddings and article metadata
embeddings = [item["embedding"] for item in data]
meta_info = [{"title": item["title"], "source": item["source"], "url": item["url"]} for item in data]

# Convert embeddings to numpy array
embedding_matrix = np.array(embeddings)

# Compute cosine similarity
similarity_matrix = cosine_similarity(embedding_matrix)

# Set threshold for similarity
threshold = 0.85

# Compute crosspost count per article
for i, article in enumerate(meta_info):
    crossposts = int(np.sum(similarity_matrix[i] > threshold)) - 1  # Exclude self-match
    article["crosspost_count"] = crossposts

# Save simplified JSON output
output_path = "output_22_5_2025/aggregated_titles_crosspost_summary.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(meta_info, f, ensure_ascii=False, indent=2)

print(f" Saved simplified crosspost summary to {output_path}")


# Extract embeddings and metadata
embeddings = [item["embedding"] for item in data]
titles = [item["title"] for item in data]

# Convert to numpy array for cosine similarity
emb_matrix = np.array(embeddings)

# Compute pairwise cosine similarity
similarities = cosine_similarity(emb_matrix)

# Define similarity threshold
threshold = 0.85

# Count how many other articles are similar to each one
for i, item in enumerate(data):
    # Exclude self-comparison by subtracting 1
    crosspost_count = int(np.sum(similarities[i] > threshold)) - 1
    item["crosspost_count"] = crosspost_count

# Save to new JSON file
with open("output_22_5_2025/aggregated_titles_with_crosspost_count.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved with crosspost counts!")




# Load previously saved summary
with open("output_22_5_2025/aggregated_titles_crosspost_summary.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

# Filter for articles crossposted on other site(s)
filtered = [a for a in articles if a["crosspost_count"] > 0]

# Save filtered results
output_path = "output_22_5_2025/crossposted_articles_gt1.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f" Saved {len(filtered)} articles with crosspost_count > 0 to {output_path}")
