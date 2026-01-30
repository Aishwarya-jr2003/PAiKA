from sentence_transformers import SentenceTransformer
import numpy as np

# Load the embedding model (downloads automatically first time)
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model loaded!\n")

# Let's test with some sentences
sentences = [
    "The dog is running in the park",
    "A puppy is playing outside",
    "The car is parked in the garage",
    "I love pizza for dinner",
    "Python is a programming language"
]

print("="*60)
print("STEP 1: Converting sentences to embeddings (vectors)")
print("="*60)

# Convert each sentence to a vector
embeddings = []
for sentence in sentences:
    embedding = model.encode(sentence)
    embeddings.append(embedding)
    print(f"\n📝 Sentence: {sentence}")
    print(f"🔢 Vector: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ... ({len(embedding)} numbers total)]")

print("\n" + "="*60)
print("STEP 2: Measuring similarity between sentences")
print("="*60)

def cosine_similarity(vec1, vec2):
    """Calculate how similar two vectors are (0 to 1)"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

# Compare sentences
print("\n🔍 Comparing: 'The dog is running' vs other sentences:\n")

for i, sentence in enumerate(sentences[1:], 1):
    similarity = cosine_similarity(embeddings[0], embeddings[i])
    
    # Visual similarity bar
    bar_length = int(similarity * 50)
    bar = "█" * bar_length + "░" * (50 - bar_length)
    
    print(f"{sentence}")
    print(f"Similarity: {similarity:.4f} {bar}")
    print()

print("="*60)
print("OBSERVATIONS:")
print("="*60)
print("✅ 'dog running' vs 'puppy playing' = HIGH similarity")
print("   (Both about animals playing)")
print()
print("❌ 'dog running' vs 'car parked' = LOW similarity")
print("   (Completely different topics)")
print()
print("🎯 The AI understands MEANING, not just words!")
print("="*60)