print("="*60)
print("UNDERSTANDING DOCUMENT CHUNKING")
print("="*60)

# Simulate a long document
document = """
Python Programming Guide

Chapter 1: Introduction
Python is a high-level programming language. It was created by Guido van Rossum in 1991.
Python emphasizes code readability and uses significant indentation.

Chapter 2: Data Structures
Lists are ordered, mutable collections. You can create a list using square brackets.
Example: my_list = [1, 2, 3, 4, 5]

List comprehensions provide a concise way to create lists. They are more Pythonic than loops.
Example: squares = [x**2 for x in range(10)]

Chapter 3: Functions
Functions are defined using the def keyword. They help organize code into reusable blocks.
Functions can accept parameters and return values.

Chapter 4: Classes
Classes provide a way to bundle data and functionality together. Creating a new class 
creates a new type of object. Classes use the class keyword.

Chapter 5: Advanced Topics
Decorators are a powerful feature in Python. They modify the behavior of functions.
Generators are functions that yield values one at a time instead of returning all at once.
""".strip()

print(f"\n📄 ORIGINAL DOCUMENT:")
print(f"   Length: {len(document)} characters")
print(f"   Words: {len(document.split())} words")
print(f"   Lines: {len(document.split(chr(10)))} lines\n")

# Method 1: No chunking (Day 4 approach)
print("="*60)
print("METHOD 1: NO CHUNKING (Send entire document)")
print("="*60)

print(f"   Chunks: 1")
print(f"   Chunk size: {len(document)} characters")
print(f"   If user asks 'What is a list comprehension?':")
print(f"   → Send ALL {len(document)} characters to AI")
print(f"   → AI must read about Introduction, Functions, Classes, etc.")
print(f"   → Lots of irrelevant information!\n")

# Method 2: Fixed-size chunking
print("="*60)
print("METHOD 2: FIXED-SIZE CHUNKING")
print("="*60)

chunk_size = 200
chunks_fixed = []
for i in range(0, len(document), chunk_size):
    chunk = document[i:i+chunk_size]
    chunks_fixed.append(chunk)

print(f"   Chunk size: {chunk_size} characters")
print(f"   Number of chunks: {len(chunks_fixed)}")
print(f"\n   Chunks created:")
for i, chunk in enumerate(chunks_fixed, 1):
    preview = chunk[:50].replace('\n', ' ')
    print(f"   {i}. {preview}... ({len(chunk)} chars)")

print(f"\n   If user asks 'What is a list comprehension?':")
print(f"   → ChromaDB finds relevant chunk (chunk 3)")
print(f"   → Send only ~200 characters")
print(f"   → Much more focused!\n")

# Method 3: Semantic chunking (by paragraph/section)
print("="*60)
print("METHOD 3: SEMANTIC CHUNKING (By chapters)")
print("="*60)

# Split by chapters
chunks_semantic = []
current_chunk = ""
for line in document.split('\n'):
    if line.startswith('Chapter'):
        if current_chunk:
            chunks_semantic.append(current_chunk.strip())
        current_chunk = line + '\n'
    else:
        current_chunk += line + '\n'
if current_chunk:
    chunks_semantic.append(current_chunk.strip())

print(f"   Number of chunks: {len(chunks_semantic)}")
print(f"\n   Chunks created:")
for i, chunk in enumerate(chunks_semantic, 1):
    first_line = chunk.split('\n')[0]
    print(f"   {i}. {first_line} ({len(chunk)} chars)")

print(f"\n   If user asks 'What is a list comprehension?':")
print(f"   → ChromaDB finds 'Chapter 2: Data Structures'")
print(f"   → Sends only that chapter")
print(f"   → Perfect context, nothing extra!\n")

# Comparison
print("="*60)
print("📊 COMPARISON")
print("="*60)

print(f"\nNo Chunking:")
print(f"   Chunks: 1")
print(f"   Precision: Low (sends everything)")
print(f"   Cost: High")

print(f"\nFixed-Size Chunking:")
print(f"   Chunks: {len(chunks_fixed)}")
print(f"   Precision: Medium (might split sentences)")
print(f"   Cost: Low")

print(f"\nSemantic Chunking:")
print(f"   Chunks: {len(chunks_semantic)}")
print(f"   Precision: High (natural boundaries)")
print(f"   Cost: Low")

print("\n" + "="*60)
print("🎯 BEST APPROACH: Semantic chunking when possible!")
print("="*60 + "\n")