from langchain_text_splitters import RecursiveCharacterTextSplitter

# Sample document
document = """
Machine Learning Fundamentals

Machine learning is a method of data analysis that automates analytical model building.
It is a branch of artificial intelligence based on the idea that systems can learn from data,
identify patterns and make decisions with minimal human intervention.

Types of Machine Learning:
1. Supervised Learning - learns from labeled data
2. Unsupervised Learning - finds patterns in unlabeled data
3. Reinforcement Learning - learns through trial and error

Applications include recommendation systems, image recognition, and natural language processing.
""" * 3  # Repeat to increase document length

print("=" * 60)
print("OPTIMIZING CHUNK SIZES")
print("=" * 60)
print(f"\n📄 Document length: {len(document)} characters\n")

# Different chunk sizes to test
chunk_sizes = [100, 300, 500, 1000]

for size in chunk_sizes:
    print(f"CHUNK SIZE: {size} characters")
    print("-" * 60)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=int(size * 0.1),  # 10% overlap
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = splitter.split_text(document)

    print(f"   Chunks created: {len(chunks)}")

    avg_len = sum(len(chunk) for chunk in chunks) / len(chunks)
    print(f"   Average chunk length: {avg_len:.0f} characters")

    # Preview first chunk
    print("   First chunk preview:")
    print(f"   {chunks[0][:80]}...")

    # Analysis
    if size < 200:
        print("   ⚠️  TOO SMALL – Context may be lost")
    elif size > 800:
        print("   ⚠️  TOO LARGE – Too much noise per chunk")
    else:
        print("   ✅ GOOD SIZE – Balanced context & precision")

    print()

print("=" * 60)
print("🎯 RECOMMENDATION")
print("=" * 60)
print("✔ Chunk size: 500–600 characters")
print("✔ Overlap: ~10% (50–60 characters)")
print("✔ Method: Recursive character splitting")
print("✔ Best for RAG, PDFs, research papers, notes")
print("=" * 60 + "\n")
