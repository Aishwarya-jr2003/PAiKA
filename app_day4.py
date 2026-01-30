import chromadb
from chromadb.config import Settings
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize ChromaDB with persistence
print("🔄 Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./paika_vectordb")
print("✅ ChromaDB ready! (Data saved to: ./paika_vectordb)\n")

# Global collection reference
collection = None

def get_or_create_collection():
    """Get existing collection or create new one"""
    global collection
    
    try:
        collection = chroma_client.get_collection("paika_documents")
        print(f"📂 Found existing collection with {collection.count()} documents\n")
    except:
        print("📝 Creating new collection...")
        collection = chroma_client.create_collection(
            name="paika_documents",
            metadata={"description": "PAiKA knowledge base"}
        )
        print("✅ New collection created!\n")

def load_documents_to_chromadb():
    """Load all .txt files into ChromaDB"""
    global collection
    
    current_dir = Path('.')
    txt_files = list(current_dir.glob('*.txt'))
    
    if not txt_files:
        print("⚠️ No .txt files found!")
        return
    
    print(f"📂 Found {len(txt_files)} text files\n")
    
    # Prepare data for ChromaDB
    documents = []
    ids = []
    metadatas = []
    
    for file in txt_files:
        try:
            content = file.read_text(encoding='utf-8')
            
            documents.append(content)
            ids.append(file.name)
            metadatas.append({
                "filename": file.name,
                "size": len(content),
                "type": "text"
            })
            
            print(f"   📄 Loaded: {file.name} ({len(content)} chars)")
        except Exception as e:
            print(f"   ❌ Failed: {file.name} - {e}")
    
    if documents:
        print(f"\n🔄 Adding {len(documents)} documents to ChromaDB...")
        print("   (ChromaDB is creating embeddings automatically...)")
        
        # ChromaDB automatically creates embeddings!
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"✅ Added {len(documents)} documents to vector database!\n")
    
def search_documents(query, n_results=3):
    """Search using ChromaDB semantic search"""
    global collection
    
    if collection is None or collection.count() == 0:
        print("❌ No documents in collection!")
        return None
    
    print(f"🔍 Searching across {collection.count()} documents...\n")
    
    # ChromaDB does all the heavy lifting!
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Display results
    print("="*60)
    print(f"📊 TOP {n_results} MOST RELEVANT DOCUMENTS:")
    print("="*60)
    
    retrieved_docs = []
    
    for i, (doc_id, doc, metadata, distance) in enumerate(zip(
        results['ids'][0],
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ), 1):
        similarity = 1 - distance
        
        print(f"\n{i}. {metadata['filename']}")
        print(f"   Similarity: {similarity:.4f}")
        print(f"   Size: {metadata['size']} characters")
        
        # Visual similarity bar
        bar_length = int(similarity * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        print(f"   {bar}")
        
        retrieved_docs.append({
            'filename': metadata['filename'],
            'content': doc,
            'similarity': similarity
        })
    
    print("\n" + "="*60 + "\n")
    
    return retrieved_docs

def ask_question_with_chromadb(question):
    """Answer question using ChromaDB RAG"""
    
    # Search for relevant documents
    relevant_docs = search_documents(question, n_results=3)
    
    if not relevant_docs:
        return "No documents found!"
    
    # Build context from retrieved documents
    context = ""
    for doc in relevant_docs:
        context += f"\n\n=== {doc['filename']} (relevance: {doc['similarity']:.2f}) ===\n"
        context += doc['content']
    
    # Create prompt
    prompt = f"""You have access to the most relevant documents for this question.

{context}

Question: {question}

Instructions:
1. Answer using information from the documents above
2. Cite which document(s) you used
3. If the answer isn't in these documents, say so

Answer:"""

    # Get AI response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def view_collection_stats():
    """Show statistics about the vector database"""
    global collection
    
    if collection is None:
        print("❌ No collection loaded!")
        return
    
    print("\n" + "="*60)
    print("📊 VECTOR DATABASE STATISTICS")
    print("="*60)
    
    count = collection.count()
    print(f"Total documents: {count}")
    
    if count > 0:
        # Get all metadata
        all_data = collection.get()
        
        total_size = sum(m['size'] for m in all_data['metadatas'])
        print(f"Total content size: {total_size:,} characters")
        
        print(f"\nDocuments in collection:")
        for i, (doc_id, metadata) in enumerate(zip(all_data['ids'], all_data['metadatas']), 1):
            print(f"   {i}. {metadata['filename']} ({metadata['size']} chars)")
    
    print("="*60 + "\n")

def clear_collection():
    """Clear all documents from collection"""
    global collection
    
    confirm = input("⚠️  Are you sure? This will delete ALL documents! (yes/no): ")
    if confirm.lower() == 'yes':
        chroma_client.delete_collection("paika_documents")
        print("✅ Collection cleared!")
        get_or_create_collection()
    else:
        print("❌ Cancelled")

def main():
    print("=" * 60)
    print("  PAiKA v0.4 - ChromaDB Vector Database Edition")
    print("  Powered by ChromaDB + Groq + RAG")
    print("=" * 60)
    print()
    
    # Initialize collection
    get_or_create_collection()
    
    # Main menu
    while True:
        print("-"*60)
        print("MENU:")
        print("1. Load documents into ChromaDB")
        print("2. Ask questions (RAG)")
        print("3. View collection statistics")
        print("4. Clear collection")
        print("5. Quit")
        print("-"*60)
        
        choice = input("\nYour choice (1-5): ").strip()
        
        if choice == '1':
            load_documents_to_chromadb()
        
        elif choice == '2':
            if collection is None or collection.count() == 0:
                print("\n❌ No documents loaded! Load documents first (option 1)\n")
                continue
            
            print("\n" + "="*60)
            print("💬 RAG Q&A MODE")
            print("="*60)
            print(f"📚 {collection.count()} documents ready in vector database")
            print("Type 'back' to return to menu\n")
            
            while True:
                question = input("💬 Your question: ").strip()
                
                if question.lower() == 'back':
                    break
                
                if not question:
                    continue
                
                print()
                try:
                    answer = ask_question_with_chromadb(question)
                    print(f"🤖 PAiKA:\n{answer}\n")
                    print("-"*60)
                except Exception as e:
                    print(f"❌ Error: {e}\n")
        
        elif choice == '3':
            view_collection_stats()
        
        elif choice == '4':
            clear_collection()
        
        elif choice == '5':
            print("\n👋 Thanks for using PAiKA! Your data is saved.")
            print("📁 Vector database location: ./paika_vectordb\n")
            break
        
        else:
            print("\n❌ Invalid choice!\n")

if __name__ == "__main__":
    main()