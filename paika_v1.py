import os
from pathlib import Path
from datetime import datetime
from collections import deque
import csv
import email
from email import policy

import chromadb
from groq import Groq
from dotenv import load_dotenv

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from langchain_text_splitters import RecursiveCharacterTextSplitter

import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
from bs4 import BeautifulSoup

# ======================================================
# ENV + CLIENT SETUP
# ======================================================
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("=" * 60)
print("  PAiKA v1.0 - Production-Ready RAG System")
print("  🎯 Complete Feature Set")
print("=" * 60)
print()

print("🔄 Initializing components...")
chroma_client = chromadb.PersistentClient(path="./paika_v1_db")
reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("✅ All systems ready!\n")

collection = None
bm25_index = None
doc_ids_list = []
conversation_history = deque(maxlen=10)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# ======================================================
# DOCUMENT LOADER
# ======================================================
class UniversalDocumentLoader:
    """Universal multi-format document loader"""

    @staticmethod
    def load_text(fp):
        try:
            return open(fp, "r", encoding="utf-8").read()
        except:
            return open(fp, "r", encoding="latin-1").read()

    @staticmethod
    def load_pdf(fp):
        try:
            with open(fp, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                if text.strip():
                    return text
        except:
            pass

        with pdfplumber.open(fp) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)

    @staticmethod
    def load_docx(fp):
        doc = DocxDocument(fp)
        return "\n".join(p.text for p in doc.paragraphs)

    @staticmethod
    def load_eml(fp):
        with open(fp, "r", encoding="utf-8") as f:
            msg = email.message_from_file(f, policy=policy.default)
        return f"From: {msg.get('From')}\nSubject: {msg.get('Subject')}\n\n{msg.get_content()}"

    @staticmethod
    def load_csv(fp):
        with open(fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = []
            for i, row in enumerate(reader, 1):
                rows.append(
                    f"Row {i}: " + ", ".join(f"{k}={v}" for k, v in row.items())
                )
        return "\n".join(rows)

    @staticmethod
    def load_html(fp):
        with open(fp, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text()

    @classmethod
    def load(cls, fp):
        ext = Path(fp).suffix.lower()
        loaders = {
            ".txt": cls.load_text,
            ".md": cls.load_text,
            ".pdf": cls.load_pdf,
            ".docx": cls.load_docx,
            ".eml": cls.load_eml,
            ".csv": cls.load_csv,
            ".html": cls.load_html,
            ".htm": cls.load_html,
        }
        if ext not in loaders:
            raise ValueError(f"Unsupported file: {ext}")
        return loaders[ext](fp), ext

# ======================================================
# DB SETUP
# ======================================================
def get_or_create_collection():
    global collection
    try:
        collection = chroma_client.get_collection("paika_v1")
        print(f"📂 Loaded collection: {collection.count()} chunks\n")
    except:
        collection = chroma_client.create_collection(
            name="paika_v1",
            metadata={"description": "PAiKA v1.0 Production"}
        )
        print("✅ Created new collection\n")

def build_bm25_index():
    global bm25_index, doc_ids_list
    if collection.count() == 0:
        return
    data = collection.get()
    doc_ids_list = data["ids"]
    tokenized = [d.lower().split() for d in data["documents"]]
    bm25_index = BM25Okapi(tokenized)

# ======================================================
# DOCUMENT INGESTION (MEMORY SAFE)
# ======================================================
def load_all_documents():
    supported = [".txt", ".md", ".pdf", ".docx", ".eml", ".csv", ".html"]
    files = []
    for ext in supported:
        files.extend(Path(".").glob(f"*{ext}"))

    if not files:
        print("⚠️ No files found\n")
        return

    chunks, ids, metas = [], [], []
    upload_date = datetime.now().strftime("%Y-%m-%d")

    for file in files:
        if file.name.startswith("~$"):
            print(f"⚠️ Skipping temp file: {file.name}")
            continue
        try:
            content, ftype = UniversalDocumentLoader.load(file)
            split = text_splitter.split_text(content)
            for i, ch in enumerate(split):
                chunks.append(ch)
                ids.append(f"{file.name}_{i}")
                metas.append({
                    "filename": file.name,
                    "file_type": ftype,
                    "chunk_index": i,
                    "total_chunks": len(split),
                    "upload_date": upload_date
                })
            print(f"✅ {file.name}: {len(split)} chunks")
        except Exception as e:
            print(f"❌ {file.name}: {e}")

    if not chunks:
        return

    print("\n🔄 Adding chunks safely (batched)...")
    BATCH = 32
    for i in range(0, len(chunks), BATCH):
        collection.add(
            documents=chunks[i:i+BATCH],
            ids=ids[i:i+BATCH],
            metadatas=metas[i:i+BATCH]
        )
        print(f"   ➕ Batch {(i//BATCH)+1}")

    build_bm25_index()
    print("✅ Ingestion complete!\n")

# ======================================================
# SEARCH + RERANK  ✅ FIXED
# ======================================================
def advanced_search(query, file_type_filter=None, k=5):
    where = {"file_type": file_type_filter} if file_type_filter else None
    sem = collection.query(query_texts=[query], n_results=20, where=where)

    sem_scores = {
        i: 1 - d for i, d in zip(sem["ids"][0], sem["distances"][0])
    }

    kw_scores = {}
    if bm25_index:
        scores = bm25_index.get_scores(query.lower().split())
        scores = scores / np.max(scores) if np.max(scores) > 0 else scores
        kw_scores = {doc_ids_list[i]: s for i, s in enumerate(scores)}

    combined = {
        i: 0.5 * sem_scores.get(i, 0) + 0.5 * kw_scores.get(i, 0)
        for i in set(sem_scores) | set(kw_scores)
    }

    top = sorted(combined, key=combined.get, reverse=True)[:20]
    docs = [collection.get(ids=[i]) for i in top]

    pairs = [(query, d["documents"][0]) for d in docs]
    rerank_scores = reranker_model.predict(pairs)

    results = []
    for score, doc in zip(rerank_scores, docs):
        results.append((float(score), doc))

    # ✅ CRITICAL FIX (no dict comparison)
    results.sort(key=lambda x: x[0], reverse=True)

    return results[:k]

# ======================================================
# ASK WITH MEMORY
# ======================================================
def ask_with_memory(q, ftype=None):
    res = advanced_search(q, ftype)

    context = ""
    for i, (_, d) in enumerate(res, 1):
        context += f"\n[Source {i}] {d['documents'][0]}"

    prompt = f"""{context}

Question: {q}
Answer:"""

    ans = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200
    ).choices[0].message.content

    conversation_history.append({"role": "User", "content": q})
    conversation_history.append({"role": "Assistant", "content": ans})

    return ans

# ======================================================
# MAIN MENU (ALL 7 OPTIONS)
# ======================================================
def main():
    get_or_create_collection()

    while True:
        print("-" * 60)
        print("1. Load documents")
        print("2. Ask questions")
        print("3. Filter search")
        print("4. View stats")
        print("5. Clear memory")
        print("6. Reset database")
        print("7. Quit")
        print("-" * 60)

        ch = input("> ").strip()

        if ch == "1":
            load_all_documents()

        elif ch == "2":
            q = input("Question: ")
            print(ask_with_memory(q))

        elif ch == "3":
            print("File types: .pdf .txt .csv .eml .html .docx")
            ft = input("File type: ").strip()
            q = input("Question: ")
            print(ask_with_memory(q, ft))

        elif ch == "4":
            print(f"Chunks: {collection.count()} | Memory: {len(conversation_history)//2}")

        elif ch == "5":
            conversation_history.clear()
            print("✅ Memory cleared")

        elif ch == "6":
            chroma_client.delete_collection("paika_v1")
            get_or_create_collection()

        elif ch == "7":
            print("👋 Exiting PAiKA")
            break

if __name__ == "__main__":
    main()

