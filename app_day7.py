import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter


# --------- File format imports ----------
import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
import email
from email import policy
import html2text
from bs4 import BeautifulSoup
import csv

# =======================================
# ENVIRONMENT SETUP
# =======================================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

groq_client = Groq(api_key=GROQ_API_KEY)

# =======================================
# CHROMADB SETUP
# =======================================
print("🔄 Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./paika_complete_db")
print("✅ ChromaDB initialized\n")

collection = None

# =======================================
# TEXT SPLITTER
# =======================================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# =======================================
# UNIVERSAL DOCUMENT LOADER
# =======================================
class UniversalDocumentLoader:
    """Supports TXT, MD, PDF, DOCX, EML, CSV, HTML"""

    @staticmethod
    def load_text(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except:
            with open(filepath, "r", encoding="latin-1") as f:
                return f.read()

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

# =======================================
# COLLECTION HANDLING
# =======================================
def get_or_create_collection():
    global collection
    try:
        collection = chroma_client.get_collection("paika_complete")
        print(f"📂 Existing collection loaded ({collection.count()} chunks)\n")
    except:
        collection = chroma_client.create_collection(
            name="paika_complete",
            metadata={"description": "PAiKA Universal RAG"}
        )
        print("📝 New collection created\n")

# =======================================
# DOCUMENT INGESTION
# =======================================
def load_all_documents():
    global collection

    supported = [".txt", ".md", ".pdf", ".docx", ".eml", ".csv", ".html", ".htm"]
    files = [f for f in Path(".").iterdir() if f.suffix.lower() in supported]

    if not files:
        print("⚠️ No supported documents found\n")
        return

    documents = []
    ids = []
    metadatas = []

    print(f"📂 Found {len(files)} files\n")

    for file in files:
        try:
            print(f"📄 Loading {file.name}")
            content, ftype = UniversalDocumentLoader.load(file)
            chunks = text_splitter.split_text(content)

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                ids.append(f"{file.name}_chunk_{i}")
                metadatas.append({
                    "filename": file.name,
                    "filetype": ftype,
                    "chunk": i,
                    "total": len(chunks)
                })

            print(f"   ✅ {len(chunks)} chunks\n")

        except Exception as e:
            print(f"   ❌ Failed: {e}\n")

    if documents:
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        print(f"🎉 Added {len(documents)} chunks to ChromaDB\n")

# =======================================
# SEARCH + ANSWER
# =======================================
def search_and_answer(question, n_results=5):
    global collection

    if collection is None or collection.count() == 0:
        return "❌ No documents loaded."

    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )

    context = ""
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context += f"\n\n[{meta['filename']} | {meta['filetype']}]\n{doc}"

    prompt = f"""
You are PAiKA, a personal AI knowledge assistant.

Use ONLY the information below to answer.

{context}

Question: {question}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content

# =======================================
# MAIN MENU
# =======================================
def main():
    print("=" * 60)
    print(" PAiKA v0.7 – Universal Document RAG")
    print(" TXT | PDF | DOCX | EMAIL | CSV | HTML | MD")
    print("=" * 60)
    print()

    get_or_create_collection()

    while True:
        print("-" * 60)
        print("1. Load all documents")
        print("2. Ask a question")
        print("3. View chunk count")
        print("4. Clear collection")
        print("5. Exit")
        print("-" * 60)

        choice = input("Enter choice (1-5): ").strip()

        if choice == "1":
            load_all_documents()

        elif choice == "2":
            if collection.count() == 0:
                print("❌ No data loaded\n")
                continue

            while True:
                q = input("\nAsk (or type 'back'): ").strip()
                if q.lower() == "back":
                    break
                print("\n🤖 PAiKA:\n")
                print(search_and_answer(q))
                print()

        elif choice == "3":
            print(f"\n📊 Total chunks: {collection.count()}\n")

        elif choice == "4":
            confirm = input("⚠️ Delete everything? (yes/no): ")
            if confirm.lower() == "yes":
                chroma_client.delete_collection("paika_complete")
                print("✅ Collection deleted\n")
                get_or_create_collection()

        elif choice == "5":
            print("\n👋 Bye!\n")
            break

        else:
            print("❌ Invalid option\n")

# =======================================
# ENTRY POINT
# =======================================
if __name__ == "__main__":
    main()














