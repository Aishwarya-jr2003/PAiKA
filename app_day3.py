from groq import Groq
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from pathlib import Path
import numpy as np

# Load environment
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load embedding model
print("🔄 Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding model ready!\n")

# Storage
documents = {}  # filename -> content
document_embeddings = {}  # filename -> embedding vector

def cosine_similarity(vec1, vec2):
    """Calculate similarity between two vectors"""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def read_file(filename):
    """Read a text file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def load_and_embed_documents():
    """Load all .txt files and create embeddings"""
    current_dir = Path('.')
    txt_files = list(current_dir.glob('*.txt'))
    
    if not txt_files:
        print("⚠️ No .txt files found!")
        return
    
    print(f"📂 Found {len(txt_files)} files. Creating embeddings...\n")
    
    for file in txt_files:
        content = read_file(file.name)
        if content:
            # Store document
            documents[file.name] = content
            
            # Create embedding
            print(f"🔄 Processing: {file.name}")
            embedding = embedding_model.encode(content)
            document_embeddings[file.name] = embedding
            
            print(f"   ✅ Embedded into {len(embedding)} dimensions")
            print(f"   📊 Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
            print()
    
    print(f"✅ Loaded and embedded {len(documents)} documents!\n")

def semantic_search(question, top_k=3):
    """Find most relevant documents using semantic similarity"""
    
    if not documents:
        return []
    
    # Convert question to embedding
    print(f"🔍 Converting question to embedding...")
    question_embedding = embedding_model.encode(question)
    print(f"   ✅ Question embedded into {len(question_embedding)} dimensions\n")
    
    # Calculate similarity with each document
    print(f"📊 Calculating similarity with each document:\n")
    similarities = []
    
    for filename, doc_embedding in document_embeddings.items():
        similarity = cosine_similarity(question_embedding, doc_embedding)
        similarities.append((filename, similarity))
        
        # Visual representation
        bar_length = int(similarity * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        print(f"   {filename}")
        print(f"   Similarity: {similarity:.4f} {bar}")
        print()
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top K most relevant
    top_docs = similarities[:top_k]
    
    print("="*60)
    print(f"🎯 TOP {top_k} MOST RELEVANT DOCUMENTS:")
    print("="*60)
    for i, (filename, score) in enumerate(top_docs, 1):
        print(f"{i}. {filename} (similarity: {score:.4f})")
    print()
    
    return top_docs

def ask_question_with_semantic_search(question):
    """Answer question using only the most relevant documents"""
    
    # Find top 3 most relevant documents
    top_docs = semantic_search(question, top_k=3)
    
    if not top_docs:
        return "No documents loaded!"
    
    # Build context from only relevant documents
    context = ""
    for filename, similarity in top_docs:
        context += f"\n\n=== {filename} (relevance: {similarity:.2f}) ===\n"
        context += documents[filename]
    
    # Create prompt
    prompt = f"""You have access to the most relevant documents for this question.

{context}

Question: {question}

Instructions:
1. Answer using ONLY the information in the documents above
2. Mention which document(s) you used
3. If the answer isn't in these documents, say so

Answer:"""

    # Get response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def compare_search_methods(question):
    """Compare old method (all docs) vs new method (semantic search)"""
    
    print("\n" + "="*60)
    print("🔬 COMPARISON: All Documents vs Semantic Search")
    print("="*60)
    
    # Method 1: Send all documents (old way)
    print("\n📚 METHOD 1: Searching ALL documents")
    print(f"   Sending {len(documents)} documents to AI")
    total_chars = sum(len(content) for content in documents.values())
    print(f"   Total characters: {total_chars:,}")
    print(f"   Cost: Higher, slower")
    
    # Method 2: Semantic search (new way)
    print("\n🎯 METHOD 2: Semantic Search")
    top_docs = semantic_search(question, top_k=3)
    relevant_chars = sum(len(documents[filename]) for filename, _ in top_docs)
    print(f"   Sending only {len(top_docs)} most relevant documents")
    print(f"   Total characters: {relevant_chars:,}")
    print(f"   Cost: Lower, faster")
    
    savings = (1 - relevant_chars / total_chars) * 100
    print(f"\n💰 SAVINGS: {savings:.1f}% less data sent to AI!")
    print("="*60 + "\n")

def main():
    print("=" * 60)
    print("  PAiKA v0.3 - Semantic Search Edition")
    print("  Powered by Embeddings + Groq")
    print("=" * 60)
    print()
    
    # Auto-load and embed all documents
    load_and_embed_documents()
    
    if not documents:
        print("❌ No documents loaded!")
        return
    
    print("="*60)
    print("💬 Ready for semantic search! Type 'quit' to exit")
    print("   Type 'compare' to see search method comparison")
    print("="*60)
    
    while True:
        question = input("\n💬 Your question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if question.lower() == 'compare':
            test_q = input("Enter a test question for comparison: ")
            compare_search_methods(test_q)
            continue
        
        if not question:
            continue
        
        print("\n" + "="*60)
        try:
            answer = ask_question_with_semantic_search(question)
            print(f"\n🤖 PAiKA:\n{answer}\n")
            print("="*60)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()