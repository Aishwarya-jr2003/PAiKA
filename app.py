from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure Groq
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("ERROR: No GROQ_API_KEY found in .env file!")
    exit()

client = Groq(api_key=api_key)

# Store all loaded documents
documents = {}

def read_file(filename):
    """Read a text file and return its contents"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None

def load_documents_from_folder():
    """Load all .txt files from current folder"""
    current_dir = Path('.')
    txt_files = list(current_dir.glob('*.txt'))
    
    if not txt_files:
        print("⚠️  No .txt files found in current folder!")
        return
    
    print(f"\n📂 Found {len(txt_files)} text files:")
    for file in txt_files:
        content = read_file(file.name)
        if content:
            documents[file.name] = content
            print(f"   ✅ Loaded: {file.name} ({len(content)} characters)")
        else:
            print(f"   ❌ Failed: {file.name}")
    
    print(f"\n✅ Total documents loaded: {len(documents)}")

def load_specific_files():
    """Let user specify which files to load"""
    print("\n📝 Enter filenames (comma-separated):")
    print("Example: file1.txt, file2.txt, file3.txt")
    
    filenames = input("Files: ").strip()
    
    if not filenames:
        print("❌ No files specified!")
        return
    
    # Split by comma and clean up
    file_list = [f.strip() for f in filenames.split(',')]
    
    print(f"\n📂 Loading {len(file_list)} files:")
    for filename in file_list:
        content = read_file(filename)
        if content:
            documents[filename] = content
            print(f"   ✅ Loaded: {filename} ({len(content)} characters)")
        else:
            print(f"   ❌ Failed: {filename}")
    
    print(f"\n✅ Total documents loaded: {len(documents)}")

def search_all_documents(question):
    """Search across all loaded documents and generate answer"""
    
    if not documents:
        return "No documents loaded! Please load documents first."
    
    # Combine all documents into one context
    combined_context = ""
    for filename, content in documents.items():
        combined_context += f"\n\n=== Document: {filename} ===\n{content}"
    
    # Create prompt with all documents
    prompt = f"""You have access to multiple documents. Answer the question based on the information in these documents.

{combined_context}

Question: {question}

Instructions:
1. Answer based ONLY on information in the documents above
2. If the answer comes from a specific document, mention which one
3. If the answer is not in any document, say so
4. Be concise but complete

Answer:"""

    # Call Groq API
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def show_loaded_documents():
    """Display all currently loaded documents"""
    if not documents:
        print("\n📭 No documents loaded yet!")
        return
    
    print("\n" + "="*50)
    print("📚 LOADED DOCUMENTS:")
    print("="*50)
    for i, (filename, content) in enumerate(documents.items(), 1):
        print(f"{i}. {filename}")
        print(f"   Size: {len(content)} characters")
        print(f"   Preview: {content[:100]}...")
        print()

def main():
    print("=" * 50)
    print("  PAiKA - Personal AI Knowledge Assistant")
    print("  Version 0.2 - Multi-Document Support")
    print("  Powered by Groq + Llama 3.3")
    print("=" * 50)
    
    # Main menu
    while True:
        print("\n" + "-"*50)
        print("MENU:")
        print("1. Load all .txt files from current folder")
        print("2. Load specific files")
        print("3. View loaded documents")
        print("4. Ask questions")
        print("5. Clear all documents")
        print("6. Quit")
        print("-"*50)
        
        choice = input("\nYour choice (1-6): ").strip()
        
        if choice == '1':
            documents.clear()
            load_documents_from_folder()
        
        elif choice == '2':
            documents.clear()
            load_specific_files()
        
        elif choice == '3':
            show_loaded_documents()
        
        elif choice == '4':
            if not documents:
                print("\n❌ No documents loaded! Load documents first (option 1 or 2)")
                continue
            
            print("\n" + "="*50)
            print("💬 ASK QUESTIONS MODE")
            print("="*50)
            print(f"📚 {len(documents)} documents ready to search")
            print("Type 'back' to return to menu\n")
            
            while True:
                question = input("💬 Your question: ").strip()
                
                if question.lower() == 'back':
                    break
                
                if not question:
                    continue
                
                print("\n🤔 Searching across all documents...\n")
                
                try:
                    answer = search_all_documents(question)
                    print(f"🤖 PAiKA:\n{answer}\n")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif choice == '5':
            documents.clear()
            print("\n✅ All documents cleared!")
        
        elif choice == '6':
            print("\n👋 Thanks for using PAiKA! Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice! Please enter 1-6")

if __name__ == "__main__":
    main()




