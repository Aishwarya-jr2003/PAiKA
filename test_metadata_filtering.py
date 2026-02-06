import chromadb
from datetime import datetime, timedelta

print("="*60)
print("METADATA FILTERING TEST")
print("="*60 + "\n")

# Create test collection
client = chromadb.Client()
collection = client.create_collection("metadata_test")

# Add documents with rich metadata
documents = [
    "Q1 planning meeting notes discussing budget allocation",
    "Email from Alice about project timeline and milestones",
    "Technical specification document for the new API",
    "Q2 budget review spreadsheet with financial projections",
    "Email from Bob requesting approval for equipment purchase"
]

metadatas = [
    {
        "file_type": ".pdf",
        "date": "2024-01-15",
        "author": "Alice",
        "category": "meeting",
        "quarter": "Q1"
    },
    {
        "file_type": ".eml",
        "date": "2024-01-20",
        "author": "Alice",
        "category": "email",
        "quarter": "Q1"
    },
    {
        "file_type": ".pdf",
        "date": "2024-01-25",
        "author": "Bob",
        "category": "technical",
        "quarter": "Q1"
    },
    {
        "file_type": ".csv",
        "date": "2024-04-10",
        "author": "Finance",
        "category": "budget",
        "quarter": "Q2"
    },
    {
        "file_type": ".eml",
        "date": "2024-01-18",
        "author": "Bob",
        "category": "email",
        "quarter": "Q1"
    }
]

collection.add(
    documents=documents,
    ids=[f"doc_{i}" for i in range(len(documents))],
    metadatas=metadatas
)

print(f"✅ Added {len(documents)} documents with metadata\n")

# Test different filters
print("="*60)
print("TEST 1: Filter by file type (emails only)")
print("="*60 + "\n")

results = collection.query(
    query_texts=["project updates"],
    n_results=10,
    where={"file_type": ".eml"}  # Only emails
)

print(f"Found {len(results['documents'][0])} results:")
for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
    print(f"{i}. {doc[:50]}...")
    print(f"   Type: {meta['file_type']}, Author: {meta['author']}\n")

print("="*60)
print("TEST 2: Filter by author (Alice's documents)")
print("="*60 + "\n")

results = collection.query(
    query_texts=["planning"],
    n_results=10,
    where={"author": "Alice"}
)

print(f"Found {len(results['documents'][0])} results:")
for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
    print(f"{i}. {doc[:50]}...")
    print(f"   Author: {meta['author']}, Date: {meta['date']}\n")

print("="*60)
print("TEST 3: Complex filter (Q1 emails)")
print("="*60 + "\n")

results = collection.query(
    query_texts=["project"],
    n_results=10,
    where={
        "$and": [
            {"file_type": ".eml"},
            {"quarter": "Q1"}
        ]
    }
)

print(f"Found {len(results['documents'][0])} Q1 emails:")
for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
    print(f"{i}. {doc[:50]}...")
    print(f"   {meta['author']}, {meta['date']}\n")

print("="*60)
print("💡 KEY INSIGHT:")
print("="*60)
print("""
Metadata filtering allows:
  ✅ Precise document selection
  ✅ Date range searches
  ✅ Author/source filtering
  ✅ Category-based retrieval
  ✅ Complex boolean queries

This makes search MUCH more targeted!
""")

client.delete_collection("metadata_test")