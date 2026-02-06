import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime

# Load environment
load_dotenv()

# Page config
st.set_page_config(
    page_title="PAiKA - AI Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background-color: #e3f2fd;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
    }
    
    .source-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'chroma_client' not in st.session_state:
    st.session_state.chroma_client = chromadb.PersistentClient(path="./paika_web_db")

if 'collection' not in st.session_state:
    try:
        st.session_state.collection = st.session_state.chroma_client.get_collection("paika_web")
    except:
        st.session_state.collection = st.session_state.chroma_client.create_collection("paika_web")

if 'groq_client' not in st.session_state:
    st.session_state.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Header
st.markdown('<h1 class="main-header">🤖 PAiKA</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.2rem;">Your Personal AI Knowledge Assistant</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Stats
    st.metric("Documents", st.session_state.collection.count())
    st.metric("Conversations", len(st.session_state.messages) // 2)
    
    st.divider()
    
    # File upload
    st.subheader("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload files",
        type=['txt', 'pdf', 'docx', 'csv', 'html'],
        accept_multiple_files=True,
        help="Upload documents to add to your knowledge base"
    )
    
    if uploaded_files:
        if st.button("Process Files", type="primary"):
            with st.spinner("Processing..."):
                for file in uploaded_files:
                    # Save file temporarily
                    temp_path = Path(f"temp_{file.name}")
                    temp_path.write_bytes(file.read())
                    
                    try:
                        # Simple text extraction
                        content = temp_path.read_text(encoding='utf-8')
                        
                        # Add to collection
                        st.session_state.collection.add(
                            documents=[content],
                            ids=[f"{file.name}_{datetime.now().timestamp()}"],
                            metadatas=[{"filename": file.name, "upload_date": str(datetime.now())}]
                        )
                        
                        st.success(f"✅ {file.name}")
                    except Exception as e:
                        st.error(f"❌ {file.name}: {e}")
                    finally:
                        temp_path.unlink(missing_ok=True)
    
    st.divider()
    
    # Clear chat
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # Reset database
    if st.button("⚠️ Reset Database"):
        st.session_state.chroma_client.delete_collection("paika_web")
        st.session_state.collection = st.session_state.chroma_client.create_collection("paika_web")
        st.session_state.messages = []
        st.success("Reset complete!")
        st.rerun()

# Main chat area
st.subheader("💬 Chat")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if "sources" in message:
            with st.expander("📚 Sources"):
                for source in message["sources"]:
                    st.markdown(f"**{source['filename']}**")
                    st.text(source['snippet'][:200] + "...")

# Chat input
if prompt := st.chat_input("Ask me anything about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Search documents
            if st.session_state.collection.count() > 0:
                results = st.session_state.collection.query(
                    query_texts=[prompt],
                    n_results=3
                )
                
                # Build context
                context = ""
                sources = []
                
                if results['documents'][0]:
                    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                        context += f"\n\n[Source {i}] {metadata['filename']}\n{doc}"
                        sources.append({
                            'filename': metadata['filename'],
                            'snippet': doc
                        })
                    
                    # Get answer
                    prompt_text = f"""Based on these documents:
{context}

Question: {prompt}

Provide a helpful answer using the information above.

Answer:"""
                    
                    response = st.session_state.groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt_text}],
                        max_tokens=1000,
                        temperature=0.7
                    )
                    
                    answer = response.choices[0].message.content
                else:
                    answer = "I don't have any documents to search. Please upload some documents first!"
                    sources = []
            else:
                answer = "Please upload documents first!"
                sources = []
            
            st.markdown(answer)
            
            # Show sources
            if sources:
                with st.expander("📚 Sources"):
                    for source in sources:
                        st.markdown(f"**{source['filename']}**")
                        st.text(source['snippet'][:200] + "...")
    
    # Add assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>PAiKA v1.0 - Built with Streamlit, ChromaDB, and Groq</p>
    <p>🚀 Production-Ready RAG System</p>
</div>
""", unsafe_allow_html=True)