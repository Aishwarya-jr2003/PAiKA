from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

documents = {}

def read_file(filename):
    """Read a text file and return its contents"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def load_documents_from_folder():
    """Load all .txt files from current folder"""
    current_dir = Path('.')
    txt_files = list(current_dir.glob('*.txt'))
    
    print(f"\n📂 Found {len(txt_files)} text files:")
    for file in txt_files:
        content = read_file(file.name)
        if content:
            documents[file.name] = content
            word_count = len(content.split())
            print(f"   ✅ {file.name} - {len(content)} chars, {word_count} words")
    
    print(f"\n✅ Loaded {len(documents)} documents total\n")

def ask_with_source_tracking(question):
    """Ask question and track which documents were most relevant"""
    
    # Build context with clear document markers
    context_parts = []
    for filename, content in documents.items():
        context_parts.append(f"""
--- START OF {filename} ---
{content}
--- END OF {filename} ---
""")
    
    full_context = "\n".join(context_parts)
    
    prompt = f"""You have access to multiple documents below. Answer the question and ALWAYS cite which document(s) you used.

{full_context}

Question: {question}

Instructions:
1. Answer the question using information from the documents
2. IMPORTANT: Mention which document(s) you got the information from
3. Use format: "According to [filename], ..." or "From [filename]: ..."
4. If information is in multiple documents, cite all relevant ones
5. If the answer isn't in any document, say "I don't have information about this in the loaded documents."

Answer:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.5
    )
    
    return response.choices[0].message.content

def smart_search(question):
    """Smarter search that shows process"""
    print(f"\n🔍 Searching across {len(documents)} documents...")
    print(f"📄 Documents: {', '.join(documents.keys())}\n")
    
    answer = ask_with_source_tracking(question)
    return answer

def main():
    print("=" * 60)
    print("  PAiKA v0.2 - Multi-Document AI Assistant")
    print("  Enhanced with Source Tracking")
    print("=" * 60)
    
    # Auto-load all .txt files
    print("\n🚀 Auto-loading all .txt files...")
    load_documents_from_folder()
    
    if not documents:
        print("❌ No .txt files found! Add some .txt files and try again.")
        return
    
    print("💬 Ready to answer questions! Type 'quit' to exit.\n")
    print("="*60)
    
    # Q&A loop
    while True:
        question = input("\n💬 Your question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not question:
            continue
        
        try:
            answer = smart_search(question)
            print(f"\n🤖 PAiKA:\n{answer}\n")
            print("-" * 60)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()