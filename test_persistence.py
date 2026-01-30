import chromadb
from chromadb.config import Settings

print("="*60)
print("CHROMADB PERSISTENCE TEST")
print("="*60)

# Create persistent client (saves to disk)
print("\n📁 Creating PERSISTENT ChromaDB client...")
client = chromadb.PersistentClient(path="./chroma_test_db")
print("   ✅ Client will save data to: ./chroma_test_db\n")

# Try to get existing collection, or create new one
try:
    collection = client.get_collection("persistent_test")
    print("📂 Found existing collection!")
    print(f"   Documents already in collection: {collection.count()}\n")
except:
    print("📝 Creating new collection...")
    collection = client.create_collection("persistent_test")
    print("   ✅ Collection created!\n")
    
    # Add some documents
    print("➕ Adding initial documents...")
    collection.add(
        documents=[
            "This document persists between runs",
            "ChromaDB saves everything to disk",
            "No need to reload every time!"
        ],
        ids=["doc1", "doc2", "doc3"]
    )
    print(f"   ✅ Added 3 documents\n")

# Query to show it works
print("🔍 Testing query...")
results = collection.query(
    query_texts=["tell me about persistence"],
    n_results=2
)

for doc in results['documents'][0]:
    print(f"   📄 {doc}")

print("\n" + "="*60)
print("💡 KEY INSIGHT:")
print("="*60)
print("Run this script AGAIN - the data will still be there!")
print("ChromaDB persisted it to disk in ./chroma_test_db")
print("\nThis means:")
print("   ✅ No need to re-index documents every time")
print("   ✅ Data survives program restarts")
print("   ✅ Production-ready persistence")
print("="*60 + "\n")