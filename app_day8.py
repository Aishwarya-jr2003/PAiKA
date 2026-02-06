import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
import numpy as np

# File loaders
import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
import email
from email import policy
import html2text
from bs4 import BeautifulSoup
import csv

# ======================================
# ENVIRONMENT
# ======================================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY missing")

groq_client = Groq(api_key=GROQ_API_KEY)

# ======================================
# CHROMADB
# ======================================
print("🔄 Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./paika_hybrid_db")
print("✅ ChromaDB ready!\n")

collection = None
bm25_index = None
doc_ids_list = []

# ======================================
# TEXT SPLITTER
# ======================================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# ======================================
# UNIVERSAL DOCUMENT LOADER
# ======================================
class UniversalDocumentLoader:

    @staticmethod
    def load_text(filepath):
        try:
            return open(filepath, "r", encoding="utf-8").read()
        except:
            return open(filepath, "r", encoding="latin-1").read()

    @staticmethod
    def load_pdf(filepath):
        text = ""
        try:
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"
            if len(text.strip()) > 100:
                return text
        except:
            pass

        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
        return text

    @staticmethod
    def load_docx(filepath):
        doc = DocxDocument(filepath)
        return "\n".join(p.text for p in doc.paragraphs)

    @staticmethod
    def load_eml(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            msg = email.message_from_file(f, policy=policy.default)

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    body = part.get_content()
                    break
                elif ctype == "text/html" and not body:
                    h = html2text.HTML2Text()
                    body = h.handle(part.get_content())
        else:
            body = msg.get_content()

        return f"""
Email
From: {msg.get('From')}
To: {msg.get('To')}
Subject: {msg.get('Subject')}
Date: {msg.get('Date')}

{body}
"""

    @staticmethod
    def load_csv(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            lines = [f"CSV FILE: {Path(filepath).name}"]
            lines.append("Columns: " + ", ".join(reader.fieldnames))
            for i, row in enumerate(reader, 1):
                lines.append(
                    f"Row {i}: " +
                    ", ".join(f"{k}={v}" for k, v in row.items() if v)
                )
        return "\n".join(lines)

    @staticmethod
    def load_html(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    @classmethod
    def load(cls, filepath):
        ext = Path(filepath).suffix.lower()
        loaders = {
            ".txt": cls.load_text,
            ".md": cls.load_text,
            ".pdf": cls.load_pdf,
            ".docx": cls.load_docx,
            ".eml": cls.load_eml,
            ".csv": cls.load_csv,
            ".html": cls.load_html,
            ".htm": cls.load_html
        }

        if ext not in loaders:
            raise ValueError(f"Unsupported file type: {ext}")

        return loaders[ext](filepath), ext

# ======================================
# COLLECTION
# ======================================
def get_or_create_collection():
    global collection
    try:
        collection = chroma_client.get_collection("paika_hybrid")
        print(f"📂 Found collection with {collection.count()} chunks\n")
    except:
        collection = chroma_client.create_collection(
            name="paika_hybrid",
            metadata={"description": "PAiKA Hybrid Search"}
        )
        print("📝 New collection created\n")

# ======================================
# BM25
# ======================================
def build_bm25_index():
    global bm25_index, doc_ids_list

    if collection is None or collection.count() == 0:
        print("⚠️ No documents to index\n")
        return

    print(f"🔄 Building BM25 index for {collection.count()} chunks...")

    data = collection.get()
    documents = data["documents"]
    doc_ids_list = data["ids"]

    tokenized_docs = [doc.lower().split() for doc in documents]
    bm25_index = BM25Okapi(tokenized_docs)

    print("✅ BM25 index built\n")

# ======================================
# LOAD DOCUMENTS
# ======================================
def load_all_documents():
    global collection

    supported = [".txt", ".md", ".pdf", ".docx", ".eml", ".csv", ".html", ".htm"]
    files = [f for f in Path(".").iterdir() if f.suffix.lower() in supported]

    if not files:
        print("⚠️ No files found\n")
        return

    documents = []
    ids = []
    metadatas = []

    print(f"📂 Found {len(files)} files\n")

    for file in files:
        if file.name.startswith("~$"):
            continue
        try:
            print(f"📄 {file.name}")
            content, ftype = UniversalDocumentLoader.load(file)
            chunks = text_splitter.split_text(content)

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                ids.append(f"{file.name}_chunk_{i}")
                metadatas.append({
                    "filename": file.name,
                    "file_type": ftype,
                    "chunk_index": i
                })

            print(f"   ✅ {len(chunks)} chunks\n")

        except Exception as e:
            print(f"   ❌ Failed: {e}\n")

    if documents:
        print(f"🔄 Adding {len(documents)} chunks...")
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        print("✅ Added to ChromaDB\n")
        build_bm25_index()

# ======================================
# HYBRID SEARCH
# ======================================
def hybrid_search(query, n_results=5, semantic_weight=0.5):
    global bm25_index

    if bm25_index is None:
        build_bm25_index()

    semantic_results = collection.query(
        query_texts=[query],
        n_results=n_results * 2
    )

    semantic_scores = {}
    for doc_id, dist in zip(
        semantic_results["ids"][0],
        semantic_results["distances"][0]
    ):
        semantic_scores[doc_id] = 1 - dist

    tokenized_query = query.lower().split()
    bm25_scores = bm25_index.get_scores(tokenized_query)

    if np.max(bm25_scores) > 0:
        bm25_scores = bm25_scores / np.max(bm25_scores)

    keyword_scores = dict(zip(doc_ids_list, bm25_scores))

    combined_scores = {}
    for doc_id in set(semantic_scores) | set(keyword_scores):
        combined_scores[doc_id] = (
            semantic_weight * semantic_scores.get(doc_id, 0.0) +
            (1 - semantic_weight) * keyword_scores.get(doc_id, 0.0)
        )

    ranked = sorted(
        combined_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:n_results]

    results = []
    for doc_id, score in ranked:
        data = collection.get(ids=[doc_id])
        results.append({
            "content": data["documents"][0],
            "metadata": data["metadatas"][0],
            "score": score
        })

    return results

# ======================================
# ASK QUESTION
# ======================================
def ask_question_hybrid(question):
    results = hybrid_search(question)

    context = ""
    for r in results:
        context += f"\n\n[{r['metadata']['filename']} | {r['score']:.2f}]\n{r['content']}"

    prompt = f"""
Use the information below to answer.

{context}

Question: {question}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )

    return response.choices[0].message.content

# ======================================
# MAIN
# ======================================
def main():
    print("=" * 60)
    print(" PAiKA v0.8 – Hybrid Search Edition")
    print("=" * 60)
    print()

    get_or_create_collection()

    while True:
        print("-" * 60)
        print("1. Load documents")
        print("2. Ask question (Hybrid)")
        print("3. Rebuild BM25 index")
        print("4. Clear all")
        print("5. Exit")
        print("-" * 60)

        choice = input("Choose (1–5): ").strip()

        if choice == "1":
            load_all_documents()

        elif choice == "2":
            question = input("Question: ").strip()
            print("\n🤖 PAiKA:\n")
            print(ask_question_hybrid(question))
            print()

        elif choice == "3":
            build_bm25_index()

        elif choice == "4":
            chroma_client.delete_collection("paika_hybrid")
            print("✅ Cleared\n")
            get_or_create_collection()

        elif choice == "5":
            print("👋 Bye!")
            break

        else:
            print("❌ Invalid choice\n")

# ======================================
# ENTRY POINT
# ======================================
if __name__ == "__main__":
    main()
