import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
import numpy as np
import time
import traceback
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Document loaders
import PyPDF2
from docx import Document as DocxDocument
from io import BytesIO

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== PAGE CONFIGURATION =====

st.set_page_config(
    page_title="PAiKA - Complete Edition",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== ADVANCED CSS =====

st.markdown("""
<style>
    /* Main header */
    .main-header {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 2rem 0;
        animation: slideDown 0.8s ease-out;
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transition: transform 0.3s;
        animation: fadeIn 0.5s;
        margin: 0.5rem 0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Success banner */
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
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat messages */
    .stChatMessage {
        animation: messageSlide 0.3s ease-out;
    }
    
    @keyframes messageSlide {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Buttons */
    .stButton > button {
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# ===== CACHED FUNCTIONS =====

@st.cache_resource(show_spinner=False)
def load_chroma_client():
    """Cache ChromaDB client"""
    return chromadb.PersistentClient(path="./paika_complete_db")

@st.cache_resource(show_spinner=False)
def load_groq_client():
    """Cache Groq client"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("❌ GROQ_API_KEY not found!")
        st.stop()
    return Groq(api_key=api_key)

@st.cache_resource(show_spinner=False)
def load_reranker_model():
    """Cache cross-encoder model"""
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

@st.cache_resource(show_spinner=False)
def load_text_splitter():
    """Cache text splitter"""
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

# ===== FILE PROCESSING =====

def process_file(file_bytes, filename):
    """Process uploaded file based on extension"""
    ext = Path(filename).suffix.lower()
    
    try:
        if ext in ['.txt', '.md']:
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
        logger.error(f"Error processing {filename}: {str(e)}")
        return None, None
    
    return None, None

# ===== INITIALIZATION =====

# Load cached resources
chroma_client = load_chroma_client()
groq_client = load_groq_client()
reranker = load_reranker_model()
text_splitter = load_text_splitter()

# Collection
try:
    collection = chroma_client.get_collection("paika_complete")
except:
    collection = chroma_client.create_collection("paika_complete")

# Session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total_queries': 0,
        'avg_response_time': 0,
        'total_files': 0,
        'total_chunks': 0,
        'usage_log': []
    }

# ===== HEADER =====

st.markdown('<h1 class="main-header">🚀 PAiKA Complete</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.3rem; margin-bottom: 2rem;">Production-Ready RAG System • Day 13 Final Edition</p>', unsafe_allow_html=True)

# ===== SIDEBAR =====

with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # Performance Dashboard
    st.subheader("⚡ Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{st.session_state.stats['total_queries']}</h3>
            <p style="margin: 0; opacity: 0.9;">Queries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_time = st.session_state.stats['avg_response_time']
        st.markdown(f"""
        <div class="metric-card">
            <h3>{avg_time:.2f}s</h3>
            <p style="margin: 0; opacity: 0.9;">Avg Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{collection.count()}</h3>
            <p style="margin: 0; opacity: 0.9;">Chunks</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{st.session_state.stats['total_files']}</h3>
            <p style="margin: 0; opacity: 0.9;">Files</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # File Upload
    st.subheader("📁 Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['txt', 'md', 'pdf', 'docx'],
        accept_multiple_files=True,
        help="Supports: TXT, MD, PDF, DOCX"
    )
    
    if uploaded_files:
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status = st.empty()
            
            start_time = time.time()
            success_count = 0
            
            for i, file in enumerate(uploaded_files):
                try:
                    status.info(f"⚙️ Processing {file.name}...")
                    
                    # Process file
                    file_bytes = file.read()
                    content, file_type = process_file(file_bytes, file.name)
                    
                    if content:
                        # Chunk content
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
                        
                        st.session_state.stats['total_chunks'] += len(chunks)
                        success_count += 1
                        status.success(f"✅ {file.name} ({len(chunks)} chunks)")
                    else:
                        status.error(f"❌ Failed: {file.name}")
                
                except Exception as e:
                    logger.error(f"Error processing {file.name}: {str(e)}")
                    status.error(f"❌ {file.name}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            elapsed = time.time() - start_time
            st.session_state.stats['total_files'] += success_count
            
            status.markdown(f"""
            <div class="success-banner">
                🎉 Processed {success_count}/{len(uploaded_files)} files in {elapsed:.2f}s!
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(2)
            st.rerun()
    
    st.divider()
    
    # Settings
    st.subheader("🔧 Settings")
    
    use_reranking = st.toggle(
        "🎯 Use Re-ranking",
        value=True,
        help="Better results, slower response"
    )
    
    use_streaming = st.toggle(
        "⚡ Stream Responses",
        value=True,
        help="See answers as they're generated"
    )
    
    n_results = st.slider(
        "📊 Results to retrieve",
        min_value=1,
        max_value=10,
        value=5,
        help="More results = better context, slower"
    )
    
    temperature = st.slider(
        "🌡️ Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher = more creative"
    )
    
    st.divider()
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("📊 Reset Stats", use_container_width=True):
        st.session_state.stats = {
            'total_queries': 0,
            'avg_response_time': 0,
            'total_files': 0,
            'total_chunks': 0,
            'usage_log': []
        }
        st.rerun()
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ===== MAIN CHAT INTERFACE =====

st.subheader("💬 Intelligent Chat")

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        
        if 'metadata' in msg and msg['metadata']:
            with st.expander("ℹ️ Details", expanded=False):
                meta = msg['metadata']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("⏱️ Response", f"{meta.get('response_time', 0):.2f}s")
                
                with col2:
                    st.metric("🔍 Search", f"{meta.get('search_time', 0):.2f}s")
                
                with col3:
                    st.metric("📚 Sources", meta.get('sources_count', 0))
                
                with col4:
                    st.metric("🎯 Reranked", "✅" if meta.get('reranked', False) else "❌")

# Chat input
if prompt := st.chat_input("Ask me anything about your documents... 💭"):
    query_start = time.time()
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        if collection.count() == 0:
            st.warning("📭 Please upload documents first!")
            answer = "No documents available. Please upload some files to get started!"
            metadata = {}
        
        else:
            try:
                # STEP 1: Search
                with st.spinner("🔍 Searching knowledge base..."):
                    search_start = time.time()
                    
                    results = collection.query(
                        query_texts=[prompt],
                        n_results=min(20, collection.count())
                    )
                    
                    search_time = time.time() - search_start
                
                if results['documents'][0]:
                    # STEP 2: Re-rank (if enabled)
                    if use_reranking:
                        with st.spinner("🎯 Re-ranking results..."):
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
                    
                    # STEP 3: Build context
                    context = ""
                    for i, result in enumerate(top_results, 1):
                        context += f"\n\n[Source {i}] {result['metadata']['filename']}\n{result['content']}"
                    
                    # STEP 4: Generate answer
                    gen_start = time.time()
                    
                    prompt_text = f"""Based on the following sources:
{context}

Question: {prompt}

Provide a comprehensive answer using the information from the sources. Be specific and cite which sources you're using."""
                    
                    if use_streaming:
                        message_placeholder = st.empty()
                        full_response = ""
                        
                        stream = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt_text}],
                            max_tokens=1500,
                            temperature=temperature,
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
                            max_tokens=1500,
                            temperature=temperature
                        )
                        answer = response.choices[0].message.content
                        st.markdown(answer)
                    
                    gen_time = time.time() - gen_start
                    
                    # Calculate metrics
                    total_time = time.time() - query_start
                    
                    # Update stats
                    st.session_state.stats['total_queries'] += 1
                    prev_avg = st.session_state.stats['avg_response_time']
                    n = st.session_state.stats['total_queries']
                    st.session_state.stats['avg_response_time'] = (prev_avg * (n-1) + total_time) / n
                    
                    # Log query
                    st.session_state.stats['usage_log'].append({
                        'query': prompt,
                        'timestamp': datetime.now(),
                        'response_time': total_time
                    })
                    
                    # Metadata
                    metadata = {
                        'response_time': total_time,
                        'search_time': search_time,
                        'rerank_time': rerank_time,
                        'gen_time': gen_time,
                        'sources_count': len(top_results),
                        'reranked': use_reranking
                    }
                
                else:
                    answer = "No relevant information found in the knowledge base."
                    metadata = {}
            
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                logger.error(traceback.format_exc())
                st.error(f"❌ Error: {str(e)}")
                answer = "I encountered an error while processing your request."
                metadata = {}
    
    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "metadata": metadata
    })

# ===== FOOTER =====

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📚 Total Chunks", collection.count())

with col2:
    st.metric("💬 Chat Messages", len(st.session_state.messages))

with col3:
    st.metric("🔍 Queries Made", st.session_state.stats['total_queries'])

with col4:
    st.metric("📁 Files Processed", st.session_state.stats['total_files'])

st.caption("🚀 PAiKA Complete Edition • Day 13 Final • Built with Streamlit + ChromaDB + Groq + Sentence Transformers")

# Keyboard shortcuts info
with st.expander("⌨️ Keyboard Shortcuts"):
    st.markdown("""
    - **Enter** in chat input: Send message
    - **Ctrl/Cmd + K**: Focus on search
    - **Esc**: Clear focus
    
    **Pro Tips:**
    - Enable re-ranking for better accuracy
    - Use streaming for real-time responses
    - Adjust temperature for creativity vs. precision
    """)