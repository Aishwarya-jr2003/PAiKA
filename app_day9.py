import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import numpy as np

import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
import email
from email import policy
import html2text
from bs4 import BeautifulSoup
import csv

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("🔄 Initializing PAiKA with Re-Ranking...")
chroma_client = chromadb.PersistentClient(path="./paika_rerank_db")
print("✅ ChromaDB ready!")

print("🔄 Loading cross-encoder for re-ranking...")
reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("✅ Re-ranker ready!\n")

collection = None
bm25_index = None
doc_ids_list = []

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

class UniversalDocumentLoader:

    @staticmethod
    def load_text(filepath):
        try:
            return open(filepath, "r", encoding="utf-8").read()
        except:
            return open(filepath, "r", encoding="latin-1").read()

    @staticmethod
    def load_pdf(filepath):
        try:
            with open(filepath, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                if len(text.strip()) > 100:
                    return text
        except:
            pass

        with pdfplumber.open(filepath) as pdf:
            text = ""
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
                if part.get_content_type() == "text/plain":
                    body = part.get_content()
                    break
        else:
            body = msg.get_content()

        return f"Email from {msg.get('From')} | Subject: {msg.get('Subject')}\n\n{body}"

    @staticmethod
    def load_csv(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            text_parts = [f"CSV: {Path(filepath).name}\nColumns: {', '.join(headers)}\n"]
            for i, row in enumerate(reader, 1):
                text_parts.append(
                    f"Row {i}: " +
                    ", ".join(f"{k}={v}" for k, v in row.items() if v)
                )
            return "\n".join(text_parts)

    @staticmethod
    def load_html(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        return soup.get_text()

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
        if ext in loaders:
            return loaders[ext](filepath), ext
        else:
            raise ValueError(f"Unsupported: {ext}")

def get_or_create_collection():
    global collection
    try:
        collection = chroma_client.get_collection("paika_rerank")
        print(f"📂 Found collection with {collection.count()} chunks\n")
    except:
        collection = chroma_client.create_collection(
            name="paika_rerank",
            metadata={"description": "PAiKA with Re-Ranking"}
        )
        print("✅ Collection created!\n")

def build_bm25_index():
    global bm25_index, doc_ids_list

    if collection.count() == 0:
        return

    print("🔄 Building BM25 index...")
    data = collection.get()
    doc_ids_list = data["ids"]
    tokenized = [doc.lower().split() for doc in data["documents"]]
    bm25_index = BM25Okapi(tokenized)
    print("✅ BM25 indexed!\n")

def load_all_documents():
    supported = [".txt", ".md", ".pdf", ".docx", ".eml", ".csv", ".html"]
    all_files = []
    for ext in supported:
        all_files.extend(list(Path(".").glob(f"*{ext}")))

    if not all_files:
        print("⚠️ No files found!\n")
        return

    all_chunks, all_ids, all_metadatas = [], [], []

    for file in all_files:
        try:
            content, file_type = UniversalDocumentLoader.load(file)
            chunks = text_splitter.split_text(content)

            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"{file.name}_chunk_{i}")
                all_metadatas.append({
                    "filename": file.name,
                    "file_type": file_type,
                    "chunk_index": i
                })

            print(f"✅ {file.name}: {len(chunks)} chunks")
        except Exception as e:
            print(f"❌ {file.name}: {e}")

    if all_chunks:
        collection.add(documents=all_chunks, ids=all_ids, metadatas=all_metadatas)
        build_bm25_index()

def search_with_reranking(query, n_retrieve=20, n_final=5):
    if collection.count() == 0:
        return []

    semantic_results = collection.query(query_texts=[query], n_results=n_retrieve)
    semantic_scores = {
        doc_id: 1 - dist
        for doc_id, dist in zip(
            semantic_results["ids"][0],
            semantic_results["distances"][0]
        )
    }

    keyword_scores = {}
    if bm25_index:
        scores = bm25_index.get_scores(query.lower().split())
        scores = scores / np.max(scores) if np.max(scores) > 0 else scores
        keyword_scores = dict(zip(doc_ids_list, scores))

    combined = {}
    for doc_id in set(semantic_scores) | set(keyword_scores):
        combined[doc_id] = 0.5 * semantic_scores.get(doc_id, 0) + 0.5 * keyword_scores.get(doc_id, 0)

    candidates = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:n_retrieve]

    docs = []
    for doc_id, score in candidates:
        data = collection.get(ids=[doc_id])
        docs.append({
            "id": doc_id,
            "content": data["documents"][0],
            "metadata": data["metadatas"][0],
            "hybrid_score": score
        })

    pairs = [(query, d["content"]) for d in docs]
    rerank_scores = reranker_model.predict(pairs)

    for d, s in zip(docs, rerank_scores):
        d["rerank_score"] = float(s)

    return sorted(docs, key=lambda x: x["rerank_score"], reverse=True)[:n_final]

def ask_question_reranked(question):
    results = search_with_reranking(question)

    context = ""
    for item in results:
        context += f"\n\n[{item['metadata']['filename']} | {item['rerank_score']:.2f}]\n{item['content']}"

    prompt = f"""
Based on these sources:
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

def main():
    print("=" * 60)
    print(" PAiKA v0.9 - Re-Ranking Edition")
    print("=" * 60)
    print()

    get_or_create_collection()

    while True:
        print("1. Load documents")
        print("2. Ask questions (with re-ranking)")
        print("3. Clear all")
        print("4. Quit")

        choice = input("Choose (1-4): ").strip()

        if choice == "1":
            load_all_documents()
        elif choice == "2":
            q = input("Question: ")
            print("\n🤖 PAiKA:\n")
            print(ask_question_reranked(q))
        elif choice == "3":
            chroma_client.delete_collection("paika_rerank")
            get_or_create_collection()
        elif choice == "4":
            break
        else:
            print("❌ Invalid")

if __name__ == "__main__":
    main()

