import chromadb

# Create a Chroma Client
chroma_client = chromadb.Client() 

# Create a collection
collection = chroma_client.create_collection(name="my_collection")
# Collections are like tables or namespaces in a vector database.
# You can store and query embeddings/documents within a collection.

# Add some text documents to the collection
collection.add(
    documents=[
        "This is a document about pineapple",
        "This is a document about oranges"
    ],
    ids=["id1", "id2"]
)

# Note: Behind the scenes, Chroma will generate embeddings for the documents
# using the default embedding model (e.g., SentenceTransformer or OpenAI if configured)

# === STEP 4: Querying the collection (you can add this part next) ===
# Example:
results = collection.query(query_texts=["Tell me about citrus fruits"], n_results=1)
print(results)

# This would return the most semantically similar document(s) to the query.