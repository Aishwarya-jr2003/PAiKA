import chromadb
from chromadb.config import Settings

print("="*60)
print("CHROMADB BASICS - HANDS-ON TUTORIAL")
print("="*60)

# Step 1: Create ChromaDB client
print("\n📦 STEP 1: Creating ChromaDB client...")
client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    allow_reset=True
))
print("   ✅ Client created!\n")

# Step 2: Create a collection (like a table in SQL)
print("📁 STEP 2: Creating a collection...")
collection = client.create_collection(
    name="test_collection",
    metadata={"description": "My first ChromaDB collection"}
)
print("   ✅ Collection 'test_collection' created!\n")

# Step 3: Add documents
print("📝 STEP 3: Adding documents...")

documents = [
    "The sky is blue and beautiful",
    "Cats are wonderful pets",
    "Python is a great programming language",
    "The ocean is vast and deep",
    "Dogs are loyal companions"
]

# ChromaDB will automatically create embeddings!
collection.add(
    documents=documents,
    ids=[f"doc_{i}" for i in range(len(documents))],
    metadatas=[{"source": f"test_{i}"} for i in range(len(documents))]
)

print(f"   ✅ Added {len(documents)} documents")
print(f"   📊 ChromaDB automatically created embeddings for each!\n")

# Step 4: Query the collection
print("🔍 STEP 4: Searching with semantic similarity...\n")

queries = [
    "Tell me about animals",
    "What about programming?",
    "Describe nature"
]

for query in queries:
    print(f"   Query: '{query}'")
    print("   " + "-"*50)
    
    # ChromaDB does embedding + similarity search automatically!
    results = collection.query(
        query_texts=[query],
        n_results=2  # Get top 2 most similar
    )
    
    for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
        similarity = 1 - distance  # Convert distance to similarity
        print(f"   {i+1}. {doc}")
        print(f"      Similarity: {similarity:.4f}")
    print()

# Step 5: Inspect what's in the collection
print("📊 STEP 5: Collection statistics...")
count = collection.count()
print(f"   Total documents: {count}")
print(f"   Collection name: {collection.name}")
print()

# Step 6: Show the magic
print("="*60)
print("✨ THE MAGIC:")
print("="*60)
print("Notice what you DIDN'T have to do:")
print("   ❌ No manual embedding creation")
print("   ❌ No manual similarity calculations")
print("   ❌ No manual sorting")
print()
print("ChromaDB did it ALL automatically!")
print("   ✅ Created embeddings")
print("   ✅ Stored them efficiently")
print("   ✅ Searched semantically")
print("   ✅ Returned best matches")
print("="*60)

# Cleanup
print("\n🧹 Cleaning up test collection...")
client.delete_collection("test_collection")
print("   ✅ Done!\n")