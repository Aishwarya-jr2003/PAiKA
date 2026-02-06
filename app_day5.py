import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --------------------------------------------------
# Environment setup
# --------------------------------------------------
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("🔄 Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./paika_chunked_db")
print("✅ ChromaDB ready!\n")

collection = None

# --------------------------------------------------
# Text splitter
# --------------------------------------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len
)

# --------------------------------------------------
# Collection helpers
# --------------------------------------------------
def get_or_create_collection():
    global collection
    try:
        collection = chroma_client.get_collection("paika_chunks")
        print(f"📂 Found existing collection with {collection.count()} chunks\n")
    except Exception:
        print("📝 Creating new chunked collection...")
        collection = chroma_client.create_collection(
            name="paika_chunks",
            metadata={"description": "PAiKA with smart chunking"}
        )
        print("✅ Collection created!\n")

# --------------------------------------------------
# Document ingestion + chunking
# --------------------------------------------------
def load_and_chunk_documents():
    global collection

    txt_files = list(Path(".").glob("*.txt"))
    if not txt_files:
        print("⚠️ No .txt files found!\n")
        return

    print(f"📂 Found {len(txt_files)} files\n")

    documents, ids, metadatas = [], [], []
    total_chunks = 0

    for file in txt_files:
        try:
            content = file.read_text(encoding="utf-8")
            chunks = text_splitter.split_text(content)

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                ids.append(f"{file.name}_chunk_{i}")
                metadatas.append({
                    "filename": file.name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk)
                })

            total_chunks += len(chunks)
            print(f"📄 {file.name} → {len(chunks)} chunks")

        except Exception as e:
            print(f"❌ Failed {file.name}: {e}")

    if documents:
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"\n✅ Added {total_chunks} chunks successfully\n")

# --------------------------------------------------
# Chunk search
# --------------------------------------------------
def search_chunks(query, n_results=5):
    if collection is None or collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=n_results)

    retrieved = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        retrieved.append({
            "filename": meta["filename"],
            "chunk_index": meta["chunk_index"],
            "content": doc,
            "similarity": 1 - dist
        })

    return retrieved

# --------------------------------------------------
# RAG QA
# --------------------------------------------------
def ask_question_with_chunks(question):
    chunks = search_chunks(question)

    if not chunks:
        return "No relevant chunks found."

    context = ""
    for c in chunks:
        context += f"\n\n[{c['filename']} | chunk {c['chunk_index']} | score {c['similarity']:.2f}]\n"
        context += c["content"]

    prompt = f"""
Use the following document chunks to answer the question.

{context}

Question: {question}

Answer clearly and cite chunks if needed.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )

    return response.choices[0].message.content

# --------------------------------------------------
# Stats
# --------------------------------------------------
def view_chunk_stats():
    if collection is None or collection.count() == 0:
        print("❌ No chunks loaded\n")
        return

    data = collection.get()
    files = {}

    for meta in data["metadatas"]:
        files.setdefault(meta["filename"], []).append(meta)

    print("\n📊 CHUNK STATS")
    for fname, metas in files.items():
        sizes = [m["chunk_size"] for m in metas]
        print(f"\n📄 {fname}")
        print(f"Chunks: {len(metas)} | Avg size: {sum(sizes)//len(sizes)} chars")

# --------------------------------------------------
# Comparison demo
# --------------------------------------------------
def compare_whole_vs_chunks():
    q = input("Enter test question: ").strip()
    chunks = search_chunks(q, n_results=3)

    if chunks:
        chars = sum(len(c["content"]) for c in chunks)
        print(f"\nRetrieved {len(chunks)} chunks ({chars} chars)")
        print("Cost: LOW | Precision: HIGH\n")

# --------------------------------------------------
# Main menu
# --------------------------------------------------
def main():
    print("=" * 60)
    print("PAiKA v0.5 — Smart Chunking Edition")
    print("=" * 60)

    get_or_create_collection()

    while True:
        print("\nMENU")
        print("1. Load & chunk documents")
        print("2. Ask questions")
        print("3. View chunk stats")
        print("4. Compare whole vs chunks")
        print("5. Clear collection")
        print("6. Quit")

        choice = input("\nChoose (1–6): ").strip()

        if choice == "1":
            load_and_chunk_documents()

        elif choice == "2":
            while True:
                q = input("\nQuestion (type 'back'): ").strip()
                if q.lower() == "back":
                    break
                try:
                    ans = ask_question_with_chunks(q)
                    print(f"\n🤖 PAIKA:\n{ans}\n")
                except Exception as e:
                    print(f"❌ Error: {e}")

        elif choice == "3":
            view_chunk_stats()

        elif choice == "4":
            compare_whole_vs_chunks()

        elif choice == "5":
            confirm = input("Delete all chunks? (yes/no): ")
            if confirm.lower() == "yes":
                chroma_client.delete_collection("paika_chunks")
                get_or_create_collection()
                print("✅ Collection cleared")

        elif choice == "6":
            print("\n👋 Goodbye!\n")
            break

        else:
            print("❌ Invalid choice")

# --------------------------------------------------
if __name__ == "__main__":
    main()
