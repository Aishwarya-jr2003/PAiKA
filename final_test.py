from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

print("="*60)
print("FINAL UNDERSTANDING TEST")
print("="*60)

# Test 1: Understand embeddings
print("\n1️⃣  What is an embedding?")
print("   ✅ A vector (list of numbers) representing text meaning")
print("   ✅ Created by a trained neural network")
print("   ✅ Captures semantic relationships\n")

text = "AI is amazing"
vec = model.encode(text)
print(f"   Example: '{text}'")
print(f"   Becomes: {len(vec)}-dimensional vector")
print(f"   First 5 values: {vec[:5]}\n")

# Test 2: Understand similarity
print("2️⃣  What does similarity mean?")
print("   ✅ How 'close' two vectors are in meaning space")
print("   ✅ Measured using cosine similarity")
print("   ✅ Range: -1 (opposite) to 1 (identical)\n")

s1 = "I love programming"
s2 = "I enjoy coding"
s3 = "I hate broccoli"

v1, v2, v3 = model.encode([s1, s2, s3])

sim_similar = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
sim_different = np.dot(v1, v3) / (np.linalg.norm(v1) * np.linalg.norm(v3))

print(f"   '{s1}' vs '{s2}'")
print(f"   Similarity: {sim_similar:.4f} (HIGH - similar meaning)\n")

print(f"   '{s1}' vs '{s3}'")
print(f"   Similarity: {sim_different:.4f} (LOW - different meaning)\n")

# Test 3: Understand why it's better
print("3️⃣  Why is semantic search better?")
print("   ✅ Finds meaning, not just keywords")
print("   ✅ Handles synonyms automatically")
print("   ✅ Understands context\n")

query = "dog"
docs = ["puppy playing", "canine running", "car driving"]
doc_vecs = model.encode(docs)
query_vec = model.encode(query)

print(f"   Search: '{query}'")
for doc, doc_vec in zip(docs, doc_vecs):
    sim = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
    print(f"   '{doc}': {sim:.4f}")

print("\n   Notice: 'puppy' and 'canine' score high even though")
print("   they don't contain the word 'dog'!\n")

print("="*60)
print("✅ YOU UNDERSTAND EMBEDDINGS!")
print("="*60)