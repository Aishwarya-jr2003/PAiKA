import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path

# ✅ Correct LangChain import (new API)
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Document loaders
import PyPDF2
import pdfplumber
from docx import Document as DocxDocument

# --------------------------------------------------
# Environment setup
# --------------------------------------------------
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("🔄 Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./paika_multiformat_db")
print("✅ ChromaDB ready!\n")

collection = None

# --------------------------------------------------
# Text splitter
# --------------------------------------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# --------------------------------------------------
# Universal Document Loader
# --------------------------------------------------
class DocumentLoader:
    """Universal document loader"""

    @staticmethod
    def load_text(filepath):
        try:
            return Path(filepath).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return Path(filepath).read_text(encoding="latin-1")

    @staticmethod
    def load_pdf(filepath):
        # Try PyPDF2 first
        try:
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = "".join(
                    page.extract_text() or "" for page in reader.pages
                )
                if len(text.strip()) > 100:
                    return text
        except Exception:
            pass

        # Fallback to pdfplumber
        try:
            with pdfplumber.open(filepath) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {e}")

    @staticmethod
    def load_docx(filepath):
        doc = DocxDocument(filepath)
        return "\n".join(p.text for p in doc.paragraphs)

    @classmethod
    def load(cls, filepath):
        ext = Path(filepath).suffix.lower()
        loaders = {
            ".txt": cls.load_text,
            ".md": cls.load_text,
            ".pdf": cls.load_pdf,
            ".docx": cls.load_docx,
        }

        if ext not in loaders:
            raise ValueError(f"Unsupported format: {ext}")

        return loaders[ext](filepath), ext

# --------------------------------------------------
# Collection helpers
# --------------------------------------------------
def get_or_create_collection():
    global collection
    try:
        collection = chroma_client.get_collection("paika_multiformat")
        print(f"📂 Found collection with {collection.count()} chunks\n")
    except Exception:
        print("📝 Creating new collection...")
        collection = chroma_client.create_collection(
            name="paika_multiformat",
            metadata={"description": "PAiKA multi-format RAG"}
        )
        print("✅ Collection created!\n")

# --------------------------------------------------
# Load & chunk documents
# --------------------------------------------------
def load_all_documents():
    global collection

    supported_exts = [".txt", ".md", ".pdf", ".docx"]
    files = [
        f for ext in supported_exts
        for f in Path(".").glob(f"*{ext}")
    ]

    if not files:
        print("⚠️ No supported documents found\n")
        return

    documents, ids, metadatas = [], [], []
    success, failed = 0, 0

    for file in files:
        try:
            print(f"📄 Processing: {file.name}")
            content, file_type = DocumentLoader.load(file)

            chunks = text_splitter.split_text(content)
            print(f"   Type: {file_type} | Chunks: {len(chunks)}")

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                ids.append(f"{file.name}_chunk_{i}")
                metadatas.append({
                    "filename": file.name,
                    "file_type": file_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk)
                })

            success += 1
            print("   ✅ Success\n")

        except Exception as e:
            failed += 1
            print(f"   ❌ Failed: {e}\n")

    if documents:
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        print(f"✅ Added {len(documents)} chunks")
        print(f"Files processed: {success}, Failed: {failed}\n")

# --------------------------------------------------
# Search + RAG answer
# --------------------------------------------------
def search_and_answer(question, n_results=5):
    if collection is None or collection.count() == 0:
        return "No documents loaded."

    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )

    retrieved = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        retrieved.append({
            "content": doc,
            "filename": meta["filename"],
            "file_type": meta["file_type"],
            "similarity": 1 - dist
        })

    context = ""
    for r in retrieved:
        context += (
            f"\n\n=== {r['filename']} "
            f"({r['file_type']}, score {r['similarity']:.2f}) ===\n"
            f"{r['content']}"
        )

    prompt = f"""
You are an AI assistant answering questions using retrieved document chunks.

{context}

Question: {question}

Instructions:
- Answer only from the provided content
- Cite document names if relevant
- If information is missing, say so

Answer:
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )

    return response.choices[0].message.content

# --------------------------------------------------
# View collection stats
# --------------------------------------------------
def view_collection_by_type():
    if collection is None or collection.count() == 0:
        print("❌ No documents loaded\n")
        return

    data = collection.get()
    grouped = {}

    for meta in data["metadatas"]:
        grouped.setdefault(meta["file_type"], set()).add(meta["filename"])

    print("\n📊 COLLECTION OVERVIEW\n")
    for ft, files in grouped.items():
        print(f"{ft.upper()} → {len(files)} files")
        for f in sorted(files):
            print(f"   - {f}")
        print()

# --------------------------------------------------
# Main menu
# --------------------------------------------------
def main():
    print("=" * 60)
    print("PAiKA v0.6 — Multi-Format Document RAG")
    print("=" * 60)

    get_or_create_collection()

    while True:
        print("\nMENU")
        print("1. Load documents")
        print("2. Ask questions")
        print("3. View collection stats")
        print("4. Clear collection")
        print("5. Quit")

        choice = input("\nChoose (1–5): ").strip()

        if choice == "1":
            load_all_documents()

        elif choice == "2":
            while True:
                q = input("\nQuestion (type 'back'): ").strip()
                if q.lower() == "back":
                    break
                try:
                    answer = search_and_answer(q)
                    print(f"\n🤖 PAiKA:\n{answer}\n")
                except Exception as e:
                    print(f"❌ Error: {e}")

        elif choice == "3":
            view_collection_by_type()

        elif choice == "4":
            if input("Delete all data? (yes/no): ").lower() == "yes":
                chroma_client.delete_collection("paika_multiformat")
                get_or_create_collection()
                print("✅ Collection cleared")

        elif choice == "5":
            print("\n👋 Goodbye!\n")
            break

        else:
            print("❌ Invalid choice")

# --------------------------------------------------
if __name__ == "__main__":
    main()
