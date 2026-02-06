from rank_bm25 import BM25Okapi
import numpy as np

print("="*60)
print("TESTING BM25 KEYWORD SEARCH")
print("="*60 + "\n")

# Sample documents
documents = [
    "Alice Johnson is the lead developer for the RAG project",
    "The Retrieval-Augmented Generation system uses vector databases",
    "Our main engineer, Alice, works on AI architectures",
    "The project lead handles all technical decisions",
    "Machine learning and RAG are important for AI"
]

print("📚 DOCUMENTS:")
print("-"*60)
for i, doc in enumerate(documents, 1):
    print(f"{i}. {doc}")
print()

# Tokenize documents (split into words)
tokenized_docs = [doc.lower().split() for doc in documents]

# Create BM25 index
print("🔄 Creating BM25 index...")
bm25 = BM25Okapi(tokenized_docs)
print("✅ Index created!\n")

# Test queries
queries = [
    "Who is the RAG project lead?",
    "Tell me about Alice",
    "What is RAG?",
    "machine learning"
]

for query in queries:
    print("="*60)
    print(f"🔍 QUERY: {query}")
    print("="*60 + "\n")
    
    # Tokenize query
    tokenized_query = query.lower().split()
    
    # Get BM25 scores
    scores = bm25.get_scores(tokenized_query)
    
    # Show scores for each document
    print("📊 BM25 SCORES:")
    print("-"*60)
    for i, (doc, score) in enumerate(zip(documents, scores), 1):
        # Highlight query words in document
        highlighted = doc
        for word in tokenized_query:
            highlighted = highlighted.replace(word, f"**{word}**")
        
        print(f"{i}. Score: {score:.4f}")
        print(f"   {highlighted}")
        print()
    
    # Get top 3 results
    top_indices = np.argsort(scores)[::-1][:3]
    
    print("🎯 TOP 3 RESULTS:")
    print("-"*60)
    for rank, idx in enumerate(top_indices, 1):
        print(f"{rank}. {documents[idx]}")
        print(f"   Score: {scores[idx]:.4f}")
        print()
    
    print()

print("="*60)
print("✅ BM25 WORKING!")
print("="*60)
print("""
OBSERVATIONS:
  - Exact word matches score higher
  - Rare words (RAG, Alice) get more weight
  - Common words (the, is) get less weight
  - This complements semantic search perfectly!
""")