import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder
import time

load_dotenv()

# Page config
st.set_page_config(
    page_title="PAiKA - Streaming Edition",
    page_icon="🤖",
    layout="wide"
)

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1.5rem 0;
        animation: fadeIn 1s;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.3rem;
        margin-bottom: 2rem;
        animation: fadeIn 1.5s;
    }
    
    .source-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        transition: transform 0.2s;
    }
    
    .source-card:hover {
        transform: translateX(5px);
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Simple document loader for streaming demo
class SimpleLoader:
    @staticmethod
    def load_text(file):
        return file.read().decode('utf-8')
    
    @staticmethod
    def load(file):
        ext = Path(file.name).suffix.lower()
        if ext in ['.txt', '.md']:
            return SimpleLoader.load_text(file), ext
        return None, None

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'chroma_client' not in st.session_state:
    st.session_state.chroma_client = chromadb.PersistentClient(path="./paika_stream_db")

if 'collection' not in st.session_state:
    try:
        st.session_state.collection = st.session_state.chroma_client.get_collection("paika_stream")
    except:
        st.session_state.collection = st.session_state.chroma_client.create_collection("paika_stream")

if 'groq_client' not in st.session_state:
    st.session_state.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

if 'text_splitter' not in st.session_state:
    st.session_state.text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

# Header
st.markdown('<h1 class="main-header">🤖 PAiKA</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">✨ Now with Streaming Responses!</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # Animated metrics
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <h3>{st.session_state.collection.count()}</h3>
            <p>Documents</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <h3>{len(st.session_state.messages) // 2}</h3>
            <p>Conversations</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Upload
    st.subheader("📁 Upload Files")
    uploaded_files = st.file_uploader(
        "Drop files here",
        type=['txt', 'md'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("🚀 Process", type="primary"):
            progress = st.progress(0)
            for i, file in enumerate(uploaded_files):
                content, file_type = SimpleLoader.load(file)
                
                if content:
                    chunks = st.session_state.text_splitter.split_text(content)
                    
                    chunk_ids = [f"{file.name}_chunk_{j}" for j in range(len(chunks))]
                    metadatas = [{
                        "filename": file.name,
                        "file_type": file_type,
                        "chunk_index": j,
                        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    } for j in range(len(chunks))]
                    
                    st.session_state.collection.add(
                        documents=chunks,
                        ids=chunk_ids,
                        metadatas=metadatas
                    )
                    
                    st.success(f"✅ {file.name}")
                
                progress.progress((i + 1) / len(uploaded_files))
            
            st.balloons()
            st.rerun()
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    
    enable_streaming = st.toggle("Enable Streaming", value=True)
    show_sources = st.toggle("Show Sources", value=True)
    n_results = st.slider("Results", 1, 10, 3)
    
    st.divider()
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main chat area
st.subheader("💬 Chat")

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if show_sources and "sources" in message and message["sources"]:
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"""
                    <div class="source-card">
                        <b>{i}. {source['filename']}</b>
                        <br><small>{source['snippet'][:150]}...</small>
                    </div>
                    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        if st.session_state.collection.count() == 0:
            st.warning("📭 Please upload documents first!")
        else:
            # Search
            with st.spinner("🔍 Searching..."):
                results = st.session_state.collection.query(
                    query_texts=[prompt],
                    n_results=min(n_results, st.session_state.collection.count())
                )
            
            if results['documents'][0]:
                # Build context
                context = ""
                sources = []
                
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                    context += f"\n\n[{i}] {metadata['filename']}\n{doc}"
                    sources.append({
                        'filename': metadata['filename'],
                        'snippet': doc
                    })
                
                # Generate with streaming
                prompt_text = f"""Based on:
{context}

Question: {prompt}

Answer concisely:"""
                
                if enable_streaming:
                    # Streaming response
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    # Get streaming response from Groq
                    stream = st.session_state.groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt_text}],
                        max_tokens=1000,
                        temperature=0.7,
                        stream=True  # Enable streaming!
                    )
                    
                    # Display tokens as they arrive
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    
                    # Final message without cursor
                    message_placeholder.markdown(full_response)
                    answer = full_response
                else:
                    # Regular response
                    response = st.session_state.groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt_text}],
                        max_tokens=1000,
                        temperature=0.7
                    )
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                
                # Show sources
                if show_sources:
                    with st.expander(f"📚 {len(sources)} Sources"):
                        for i, source in enumerate(sources, 1):
                            st.markdown(f"""
                            <div class="source-card">
                                <b>{i}. {source['filename']}</b>
                                <br><small>{source['snippet'][:150]}...</small>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                answer = "No relevant information found."
                sources = []
                st.info(answer)
    
    # Save to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources if show_sources else []
    })

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🚀 PAiKA with Streaming • Built with Streamlit & Groq</p>
</div>
""", unsafe_allow_html=True)