import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
import numpy as np
import time
import hashlib

# Document loaders
import PyPDF2
from docx import Document as DocxDocument
from io import BytesIO

load_dotenv()

# Page config
st.set_page_config(
    page_title="PAiKA Optimized",
    page_icon="⚡",
    layout="wide"
)

# CSS with animations
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
        animation: slideDown 0.8s ease-out;
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transition: transform 0.3s;
        animation: fadeIn 0.5s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .success-banner {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-weight: bold;
        animation: slideIn 0.5s;
    }
    
    @keyframes slideIn {
        from { transform: translateX(-100%); }
        to { transform: translateX(0); }
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# ===== CACHED FUNCTIONS FOR PERFORMANCE =====

@st.cache_resource(show_spinner=False)
def load_chroma_client():
    """Cache ChromaDB client - only initialize once"""
    return chromadb.PersistentClient(path="./paika_optimized_db")

@st.cache_resource(show_spinner=False)
def load_groq_client():
    """Cache Groq client"""
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

@st.cache_resource(show_spinner=False)
def load_reranker_model():
    """Cache cross-encoder model - expensive to load"""
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

@st.cache_resource(show_spinner=False)
def load_text_splitter():
    """Cache text splitter"""
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

@st.cache_data(show_spinner=False)
def process_file_cached(file_bytes, filename):
    """Cache file processing based on content hash"""
    # This prevents re-processing the same file
    return process_file_content(file_bytes, filename)

def process_file_content(file_bytes, filename):
    """Process file and return content"""
    ext = Path(filename).suffix.lower()
    
    try:
        if ext == '.txt' or ext == '.md':
            return file_bytes.decode('utf-8'), ext
        elif ext == '.pdf':
            pdf = PyPDF2.PdfReader(BytesIO(file_bytes))
            content = "\n".join([page.extract_text() for page in pdf.pages])
            return content, ext
        elif ext == '.docx':
            doc = DocxDocument(BytesIO(file_bytes))
            content = "\n".join([p.text for p in doc.paragraphs])
            return content, ext
    except Exception as e:
        st.error(f"Error processing {filename}: {e}")
        return None, None
    
    return None, None

# ===== INITIALIZE WITH CACHING =====

chroma_client = load_chroma_client()
groq_client = load_groq_client()
reranker = load_reranker_model()
text_splitter = load_text_splitter()

# Collection
try:
    collection = chroma_client.get_collection("paika_opt")
except:
    collection = chroma_client.create_collection("paika_opt")

# Session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'performance_stats' not in st.session_state:
    st.session_state.performance_stats = {
        'total_queries': 0,
        'avg_response_time': 0,
        'total_files_processed': 0,
        'cache_hits': 0
    }

# Header
st.markdown('<h1 class="main-header">⚡ PAiKA Optimized</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.2rem;">Lightning Fast RAG with Advanced Caching</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Control Center")
    
    # Performance metrics
    st.subheader("⚡ Performance")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{st.session_state.performance_stats['total_queries']}</h2>
            <p>Queries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_time = st.session_state.performance_stats['avg_response_time']
        st.markdown(f"""
        <div class="metric-card">
            <h2>{avg_time:.2f}s</h2>
            <p>Avg Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Upload with progress
    st.subheader("📁 Upload Files")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['txt', 'md', 'pdf', 'docx'],
        accept_multiple_files=True,
        help="Optimized processing with caching"
    )
    
    if uploaded_files:
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            
            start_time = time.time()
            
            for i, file in enumerate(uploaded_files):
                status_placeholder.info(f"⚙️ Processing {file.name}...")
                
                # Read file bytes once
                file_bytes = file.read()
                
                # Process with caching
                content, file_type = process_file_cached(file_bytes, file.name)
                
                if content:
                    # Chunk
                    chunks = text_splitter.split_text(content)
                    
                    # Add to collection
                    timestamp = datetime.now().timestamp()
                    chunk_ids = [f"{file.name}_{timestamp}_{j}" for j in range(len(chunks))]
                    metadatas = [{
                        "filename": file.name,
                        "file_type": file_type,
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    } for j in range(len(chunks))]
                    
                    collection.add(
                        documents=chunks,
                        ids=chunk_ids,
                        metadatas=metadatas
                    )
                    
                    st.session_state.performance_stats['total_files_processed'] += 1
                    status_placeholder.success(f"✅ {file.name} ({len(chunks)} chunks)")
                else:
                    status_placeholder.error(f"❌ Failed: {file.name}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            elapsed = time.time() - start_time
            status_placeholder.markdown(f"""
            <div class="success-banner">
                🎉 Processed {len(uploaded_files)} files in {elapsed:.2f}s!
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(2)
            st.rerun()
    
    st.divider()
    
    # Settings
    st.subheader("🔧 Settings")
    
    use_reranking = st.toggle("Use Re-ranking", value=True, help="Slower but more accurate")
    use_streaming = st.toggle("Streaming Responses", value=True)
    n_results = st.slider("Results", 1, 10, 5)
    
    st.divider()
    
    # Actions
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("📊 Reset Stats", use_container_width=True):
        st.session_state.performance_stats = {
            'total_queries': 0,
            'avg_response_time': 0,
            'total_files_processed': 0,
            'cache_hits': 0
        }
        st.rerun()

# Main chat
st.subheader("💬 Chat")

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        
        if 'metadata' in msg and msg['metadata']:
            with st.expander(f"ℹ️ Details"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Response Time", f"{msg['metadata'].get('response_time', 0):.2f}s")
                with col2:
                    st.metric("Sources", msg['metadata'].get('sources_count', 0))
                with col3:
                    st.metric("Reranked", "Yes" if msg['metadata'].get('reranked', False) else "No")

# Chat input
if prompt := st.chat_input("Ask anything..."):
    # Start timing
    query_start = time.time()
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        if collection.count() == 0:
            st.warning("📭 Please upload documents first!")
            answer = "No documents available."
            metadata = {}
        else:
            with st.spinner("🔍 Searching..."):
                # Search
                search_start = time.time()
                results = collection.query(
                    query_texts=[prompt],
                    n_results=min(20, collection.count())
                )
                search_time = time.time() - search_start
                
                if results['documents'][0]:
                    # Re-rank if enabled
                    if use_reranking:
                        rerank_start = time.time()
                        
                        candidates = [{
                            'content': doc,
                            'metadata': meta
                        } for doc, meta in zip(results['documents'][0], results['metadatas'][0])]
                        
                        pairs = [(prompt, c['content']) for c in candidates]
                        scores = reranker.predict(pairs)
                        
                        for cand, score in zip(candidates, scores):
                            cand['score'] = float(score)
                        
                        candidates.sort(key=lambda x: x['score'], reverse=True)
                        top_results = candidates[:n_results]
                        
                        rerank_time = time.time() - rerank_start
                    else:
                        top_results = [{
                            'content': doc,
                            'metadata': meta,
                            'score': 1 - dist
                        } for doc, meta, dist in zip(
                            results['documents'][0][:n_results],
                            results['metadatas'][0][:n_results],
                            results['distances'][0][:n_results]
                        )]
                        rerank_time = 0
                    
                    # Build context
                    context = ""
                    for i, result in enumerate(top_results, 1):
                        context += f"\n\n[{i}] {result['metadata']['filename']}\n{result['content']}"
                    
                    # Generate answer
                    gen_start = time.time()
                    
                    prompt_text = f"""Based on:
{context}

Question: {prompt}

Provide a helpful answer:"""
                    
                    if use_streaming:
                        message_placeholder = st.empty()
                        full_response = ""
                        
                        stream = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt_text}],
                            max_tokens=1000,
                            temperature=0.7,
                            stream=True
                        )
                        
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                message_placeholder.markdown(full_response + "▌")
                        
                        message_placeholder.markdown(full_response)
                        answer = full_response
                    else:
                        response = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt_text}],
                            max_tokens=1000,
                            temperature=0.7
                        )
                        answer = response.choices[0].message.content
                        st.markdown(answer)
                    
                    gen_time = time.time() - gen_start
                    
                    # Calculate total time
                    total_time = time.time() - query_start
                    
                    # Update stats
                    st.session_state.performance_stats['total_queries'] += 1
                    prev_avg = st.session_state.performance_stats['avg_response_time']
                    n = st.session_state.performance_stats['total_queries']
                    st.session_state.performance_stats['avg_response_time'] = (prev_avg * (n-1) + total_time) / n
                    
                    # Metadata
                    metadata = {
                        'response_time': total_time,
                        'search_time': search_time,
                        'rerank_time': rerank_time if use_reranking else 0,
                        'gen_time': gen_time,
                        'sources_count': len(top_results),
                        'reranked': use_reranking
                    }
                    
                    # Show timing breakdown
                    with st.expander("⏱️ Performance Breakdown"):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Search", f"{search_time:.2f}s")
                        with col2:
                            st.metric("Re-rank", f"{rerank_time:.2f}s" if use_reranking else "Disabled")
                        with col3:
                            st.metric("Generate", f"{gen_time:.2f}s")
                        with col4:
                            st.metric("Total", f"{total_time:.2f}s")
                else:
                    answer = "No relevant information found."
                    metadata = {}
    
    # Save message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "metadata": metadata
    })

# Footer
st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📚 Documents", collection.count())
with col2:
    st.metric("💬 Messages", len(st.session_state.messages))
with col3:
    cache_info = f"{st.session_state.performance_stats['cache_hits']} hits"
    st.metric("💾 Cache", cache_info)

st.caption("⚡ Optimized with caching, re-ranking, and streaming • Built with Streamlit")