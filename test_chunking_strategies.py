from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter
)

# Sample document
document = """
Artificial Intelligence Fundamentals

Introduction to AI
Artificial Intelligence (AI) is the simulation of human intelligence by machines.
It has become one of the most important technologies of the 21st century.

Machine Learning
Machine learning is a subset of AI that enables systems to learn from data.
Instead of being explicitly programmed, ML systems improve through experience.

Types of Machine Learning
There are three main types: supervised learning, unsupervised learning, and
reinforcement learning. Each has different applications and use cases.

Neural Networks
Neural networks are inspired by biological neurons in the human brain.
They consist of layers of interconnected nodes that process information.

Deep Learning
Deep learning uses neural networks with many layers. It has revolutionized
computer vision, natural language processing, and many other fields.

Applications
AI is used in healthcare, finance, transportation, and entertainment.
Self-driving cars and virtual assistants are common examples.
"""

print("=" * 60)
print("TESTING CHUNKING STRATEGIES")
print("=" * 60)
print(f"\n📄 Original document length: {len(document)} characters\n")

# ------------------------------------------------------------------
# Strategy 1: Character-based splitter
# ------------------------------------------------------------------
print("STRATEGY 1: Character Text Splitter")
print("-" * 60)

char_splitter = CharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20,
    separator="\n"
)

char_chunks = char_splitter.split_text(document)
print(f"Chunks created: {len(char_chunks)}")

for i, chunk in enumerate(char_chunks[:3], start=1):
    print(f"\nChunk {i}:")
    print(chunk[:100] + "...")
    print(f"Length: {len(chunk)} characters")

# ------------------------------------------------------------------
# Strategy 2: Recursive Character Splitter (RECOMMENDED)
# ------------------------------------------------------------------
print("\n" + "=" * 60)
print("STRATEGY 2: Recursive Character Text Splitter (BEST)")
print("-" * 60)

recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20,
    separators=["\n\n", "\n", ". ", " ", ""]
)

recursive_chunks = recursive_splitter.split_text(document)
print(f"Chunks created: {len(recursive_chunks)}")

for i, chunk in enumerate(recursive_chunks[:3], start=1):
    print(f"\nChunk {i}:")
    print(chunk[:100] + "...")
    print(f"Length: {len(chunk)} characters")

# ------------------------------------------------------------------
# Strategy 3: Token-based splitter
# ------------------------------------------------------------------
print("\n" + "=" * 60)
print("STRATEGY 3: Token Text Splitter")
print("-" * 60)

token_splitter = TokenTextSplitter(
    chunk_size=50,
    chunk_overlap=10
)

token_chunks = token_splitter.split_text(document)
print(f"Chunks created: {len(token_chunks)}")

for i, chunk in enumerate(token_chunks[:3], start=1):
    print(f"\nChunk {i}:")
    print(chunk[:100] + "...")
    print(f"Approx tokens: {len(chunk.split())}")

# ------------------------------------------------------------------
# Comparison
# ------------------------------------------------------------------
print("\n" + "=" * 60)
print("📊 COMPARISON SUMMARY")
print("=" * 60)
print(f"Character Splitter: {len(char_chunks)} chunks")
print(f"Recursive Splitter: {len(recursive_chunks)} chunks")
print(f"Token Splitter: {len(token_chunks)} chunks")

print("\n🎯 WINNER: Recursive Character Text Splitter")
print("✅ Preserves semantic structure")
print("✅ Flexible separators")
print("✅ Best choice for RAG pipelines")
print("=" * 60)
