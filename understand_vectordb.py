import time
import numpy as np

print("="*60)
print("UNDERSTANDING VECTOR DATABASES")
print("="*60)

# Simulate documents
num_docs = 1000
print(f"\n📚 Imagine we have {num_docs} documents\n")

# Method 1: Manual search (what we did Day 3)
print("METHOD 1: Manual Search")
print("-" * 60)

start = time.time()
# Simulate checking every document
for i in range(num_docs):
    # Simulate similarity calculation
    similarity = np.random.random()

# Find top 5
comparisons_manual = num_docs
end = time.time()

print(f"   Comparisons needed: {comparisons_manual}")
print(f"   Time: {(end-start)*1000:.2f}ms")
print(f"   Method: Check EVERY document\n")

# Method 2: Vector DB (ChromaDB)
print("METHOD 2: Vector Database (Indexed)")
print("-" * 60)

start = time.time()
# ChromaDB uses HNSW - only checks ~log(n) documents
comparisons_db = int(np.log2(num_docs)) * 3  # Approximate

# Simulate optimized search
for i in range(comparisons_db):
    similarity = np.random.random()

end = time.time()

print(f"   Comparisons needed: {comparisons_db}")
print(f"   Time: {(end-start)*1000:.2f}ms")
print(f"   Method: Use index to skip irrelevant docs\n")

# Comparison
speedup = comparisons_manual / comparisons_db
print("="*60)
print(f"🚀 SPEEDUP: {speedup:.1f}x faster!")
print(f"💰 EFFICIENCY: {(1 - comparisons_db/comparisons_manual)*100:.1f}% fewer comparisons")
print("="*60)

print("\n💡 KEY INSIGHT:")
print("   Vector databases use smart indexing algorithms")
print("   to avoid checking every single document!")
print("\n   It's like using a book's index instead of")
print("   reading every page to find a topic.\n")