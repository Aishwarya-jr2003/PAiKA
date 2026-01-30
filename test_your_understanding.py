from sentence_transformers import SentenceTransformer
import numpy as np

# Load model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model loaded successfully!\n")

# Cosine similarity function
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

print("=" * 60)
print("QUIZ: Predict which sentence pairs are SIMILAR")
print("=" * 60)

# Sentence pairs
pairs = [
    ("I love programming", "I enjoy coding"),
    ("The weather is nice", "It's a beautiful day"),
    ("Python is great", "I like pizza"),
    ("Machine learning is hard", "AI is difficult"),
    ("The car is red", "The sky is blue")
]

print("\nHere are the sentence pairs:\n")

for i, (s1, s2) in enumerate(pairs, 1):
    print(f"{i}. '{s1}'  <-->  '{s2}'")

input("\n🧠 Make your guesses, then press Enter to see results...")

print("\n" + "=" * 60)
print("RESULTS:")
print("=" * 60 + "\n")

for sent1, sent2 in pairs:
    vec1 = model.encode(sent1)
    vec2 = model.encode(sent2)
    similarity = cosine_similarity(vec1, vec2)

    if similarity > 0.7:
        label = "🔥 VERY SIMILAR"
    elif similarity > 0.5:
        label = "✅ SIMILAR"
    elif similarity > 0.3:
        label = "🤔 SOMEWHAT RELATED"
    else:
        label = "❌ NOT RELATED"

    print(f"'{sent1}'")
    print("   vs")
    print(f"'{sent2}'")
    print(f"→ Similarity: {similarity:.4f} {label}\n")

print("=" * 60)
print("🎯 The model understands MEANING, not just keywords!")
print("=" * 60)
