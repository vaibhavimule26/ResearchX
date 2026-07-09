import chromadb

# Create ChromaDB client
client = chromadb.PersistentClient(path="chroma_db")

# Create (or load) collection
collection = client.get_or_create_collection(
    name="research_papers"
)