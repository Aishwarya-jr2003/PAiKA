import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter

from sentence_transformers import CrossEncoder
import time
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import logging
import traceback

# Document loaders
import PyPDF2
from docx import Document as DocxDocument
from io import BytesIO

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="PAiKA Complete",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
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
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    
    .success-banner {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
    }
    
    .keyboard-hint {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# ===== CACHED FUNCTIONS =====

@st.cache_resource(show_spinner=False)
def load_chroma_client():
    return chromadb.PersistentClient(path="./paika_complete_db")

@st.cache_resource
def load_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except KeyError:
        st.error("❌ GROQ_API_KEY not found in Streamlit secrets")
        st.stop()

    if not api_key or not isinstance(api_key, str):
        st.error("❌ Invalid GROQ_API_KEY")
        st.stop()

    # ✅ Groq SDK expects key in environment
    os.environ["GROQ_API_KEY"] = api_key

    # ✅ Instantiate WITHOUT arguments
    return Groq()

@st.cache_resource(show_spinner=False)
def load_reranker_model():
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

@st.cache_resource(show_spinner=False)
def load_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

# ===== HELPER FUNCTIONS =====

def process_file_content(file_bytes, filename):
    """Process file and return content"""
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
        logger.error(f"Error processing {filename}: {e}")
        return None, None
    
    return None, None

def load_usage_log():
    try:
        with open('./usage_log.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_usage_log(log):
    with open('./usage_log.json', 'w') as f:
        json.dump(log, f)

# ===== INITIALIZE =====

chroma_client = load_chroma_client()
groq_client = load_groq_client()
reranker = load_reranker_model()
text_splitter = load_text_splitter()

try:
    collection = chroma_client.get_collection("paika_complete")
except:
    collection = chroma_client.create_collection("paika_complete")

# Session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'usage_log' not in st.session_state:
    st.session_state.usage_log = load_usage_log()

if 'performance_stats' not in st.session_state:
    st.session_state.performance_stats = {
        'total_queries': 0,
        'avg_response_time': 0,
        'total_files_processed': 0,
        'cache_hits': 0
    }

if 'show_keyboard_shortcuts' not in st.session_state:
    st.session_state.show_keyboard_shortcuts = False

# ===== HEADER =====

st.markdown('<h1 class="main-header">🚀 PAiKA Complete</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.2rem;">Production-Ready RAG System with Analytics</p>', unsafe_allow_html=True)

# ===== SIDEBAR =====

with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # Quick stats
    st.subheader("📊 Quick Stats")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{collection.count()}</h3>
            <p>Chunks</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(st.session_state.usage_log)}</h3>
            <p>Queries</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # File upload
    st.subheader("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['txt', 'md', 'pdf', 'docx'],
        accept_multiple_files=True,
        help="Supported: TXT, MD, PDF, DOCX"
    )
    
    if uploaded_files:
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status = st.empty()
            
            start_time = time.time()
            success_count = 0
            error_count = 0
            
            for i, file in enumerate(uploaded_files):
                try:
                    status.info(f"⚙️ Processing {file.name}...")
                    
                    file_bytes = file.read()
                    content, file_type = process_file_content(file_bytes, file.name)
                    
                    if content and len(content.strip()) > 0:
                        chunks = text_splitter.split_text(content)
                        
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
                        
                        success_count += 1
                        status.success(f"✅ {file.name} ({len(chunks)} chunks)")
                    else:
                        error_count += 1
                        status.error(f"❌ {file.name} is empty")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing {file.name}: {e}")
                    status.error(f"❌ {file.name}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            elapsed = time.time() - start_time
            
            if success_count > 0:
                st.balloons()
                status.markdown(f"""
                <div class="success-banner">
                    🎉 {success_count} files processed in {elapsed:.2f}s!
                </div>
                """, unsafe_allow_html=True)
            
            if error_count > 0:
                st.warning(f"⚠️ {error_count} files failed")
            
            st.session_state.performance_stats['total_files_processed'] += success_count
            time.sleep(2)
            st.rerun()
    
    st.divider()
    
    # Settings
    st.subheader("🔧 Settings")
    
    use_reranking = st.toggle(
        "Use Re-ranking",
        value=True,
        help="Slower but more accurate results"
    )
    
    use_streaming = st.toggle(
        "Streaming Responses",
        value=True,
        help="Display responses as they generate"
    )
    
    n_results = st.slider(
        "Number of Results",
        min_value=1,
        max_value=10,
        value=5,
        help="More results = better context but slower"
    )
    
    st.divider()
    
    # Keyboard shortcuts toggle
    if st.button("⌨️ Keyboard Shortcuts", use_container_width=True):
        st.session_state.show_keyboard_shortcuts = not st.session_state.show_keyboard_shortcuts
    
    if st.session_state.show_keyboard_shortcuts:
        st.markdown("""
        <div class="keyboard-hint">
        <b>Shortcuts:</b><br>
        • Ctrl+K: Focus search<br>
        • Ctrl+N: New chat<br>
        • Ctrl+S: Export data<br>
        • Ctrl+/: Show this help
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("📊 Reset Stats", use_container_width=True):
            st.session_state.performance_stats = {
                'total_queries': 0,
                'avg_response_time': 0,
                'total_files_processed': 0,
                'cache_hits': 0
            }
            st.session_state.usage_log = []
            save_usage_log([])
            st.rerun()
    
    if st.button("💾 Export All Data", use_container_width=True, type="primary"):
        export_data = {
            'total_chunks': collection.count(),
            'total_queries': len(st.session_state.usage_log),
            'performance_stats': st.session_state.performance_stats,
            'usage_log': st.session_state.usage_log
        }
        st.download_button(
            "📥 Download",
            json.dumps(export_data, indent=2),
            "paika_export.json",
            "application/json",
            use_container_width=True
        )

# ===== MAIN CONTENT =====

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Analytics", "📚 Documents"])

with tab1:
    st.subheader("Chat with Your Documents")
    
    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            
            if 'metadata' in msg and msg['metadata']:
                with st.expander("ℹ️ Details"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Time", f"{msg['metadata'].get('response_time', 0):.2f}s")
                    with col2:
                        st.metric("Sources", msg['metadata'].get('sources_count', 0))
                    with col3:
                        st.metric("Reranked", "✓" if msg['metadata'].get('reranked') else "✗")
    
    # Chat input
    if prompt := st.chat_input("Ask anything about your documents..."):
        query_start = time.time()
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if collection.count() == 0:
                answer = "📭 Please upload documents first!"
                metadata = {}
                success = False
            else:
                try:
                    with st.spinner("🔍 Searching..."):
                        search_start = time.time()
                        results = collection.query(
                            query_texts=[prompt],
                            n_results=min(20, collection.count())
                        )
                        search_time = time.time() - search_start
                        
                        if results['documents'][0]:
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
                            
                            context = ""
                            for i, result in enumerate(top_results, 1):
                                context += f"\n\n[{i}] {result['metadata']['filename']}\n{result['content']}"
                            
                            gen_start = time.time()
                            
                            prompt_text = f"""Based on the following information:
{context}

Question: {prompt}

Provide a helpful and accurate answer:"""
                            
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
                            total_time = time.time() - query_start
                            
                            metadata = {
                                'response_time': total_time,
                                'search_time': search_time,
                                'rerank_time': rerank_time,
                                'gen_time': gen_time,
                                'sources_count': len(top_results),
                                'reranked': use_reranking
                            }
                            
                            success = True
                            
                            with st.expander("⏱️ Performance"):
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Search", f"{search_time:.2f}s")
                                with col2:
                                    st.metric("Rerank", f"{rerank_time:.2f}s" if use_reranking else "Off")
                                with col3:
                                    st.metric("Generate", f"{gen_time:.2f}s")
                                with col4:
                                    st.metric("Total", f"{total_time:.2f}s")
                        else:
                            answer = "No relevant information found."
                            metadata = {}
                            success = False
                
                except Exception as e:
                    logger.error(f"Query error: {e}")
                    logger.error(traceback.format_exc())
                    answer = f"❌ Error: {str(e)}"
                    metadata = {}
                    success = False
                    st.error(answer)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "metadata": metadata
        })
        
        # Log usage
        st.session_state.usage_log.append({
            'timestamp': datetime.now().isoformat(),
            'query': prompt,
            'response_time': metadata.get('response_time', 0),
            'success': success
        })
        save_usage_log(st.session_state.usage_log)
        
        # Update stats
        st.session_state.performance_stats['total_queries'] += 1
        prev_avg = st.session_state.performance_stats['avg_response_time']
        n = st.session_state.performance_stats['total_queries']
        st.session_state.performance_stats['avg_response_time'] = \
            (prev_avg * (n-1) + metadata.get('response_time', 0)) / n
        
        st.rerun()

with tab2:
    st.subheader("📊 System Analytics")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_chunks = collection.count()
    total_queries = len(st.session_state.usage_log)
    avg_response = st.session_state.performance_stats['avg_response_time']
    
    successful = sum(1 for q in st.session_state.usage_log if q.get('success', False))
    success_rate = (successful / total_queries * 100) if total_queries > 0 else 0
    
    with col1:
        st.metric("📄 Chunks", total_chunks)
    with col2:
        st.metric("💬 Queries", total_queries)
    with col3:
        st.metric("⚡ Avg Time", f"{avg_response:.2f}s")
    with col4:
        st.metric("✅ Success", f"{success_rate:.1f}%")
    
    if st.session_state.usage_log:
        st.divider()
        
        # Usage trends
        df_usage = pd.DataFrame([
            {
                'timestamp': datetime.fromisoformat(q['timestamp']),
                'response_time': q.get('response_time', 0),
                'success': q.get('success', False)
            }
            for q in st.session_state.usage_log
        ])
        
        df_usage['date'] = df_usage['timestamp'].dt.date
        daily_queries = df_usage.groupby('date').size().reset_index(name='queries')
        
        fig = px.line(
            daily_queries,
            x='date',
            y='queries',
            title='Query Activity Over Time'
        )
        fig.update_traces(line_color='#667eea', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_time = px.histogram(
                df_usage,
                x='response_time',
                title='Response Time Distribution'
            )
            fig_time.update_traces(marker_color='#764ba2')
            st.plotly_chart(fig_time, use_container_width=True)
        
        with col2:
            success_count = df_usage['success'].value_counts()
            fig_success = go.Figure(data=[go.Pie(
                labels=['Success', 'Failed'],
                values=[success_count.get(True, 0), success_count.get(False, 0)],
                hole=0.4
            )])
            st.plotly_chart(fig_success, use_container_width=True)
    else:
        st.info("📊 Start chatting to see analytics!")

with tab3:
    st.subheader("📚 Document Library")
    
    if total_chunks > 0:
        all_data = collection.get()
        
        file_types = Counter()
        files_info = {}
        
        for meta in all_data['metadatas']:
            ftype = meta.get('file_type', 'unknown')
            fname = meta.get('filename', 'Unknown')
            
            file_types[ftype] += 1
            
            if fname not in files_info:
                files_info[fname] = {
                    'chunks': 0,
                    'type': ftype,
                    'date': meta.get('upload_date', 'Unknown')
                }
            files_info[fname]['chunks'] += 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_types = go.Figure(data=[go.Pie(
                labels=list(file_types.keys()),
                values=list(file_types.values()),
                hole=0.4
            )])
            fig_types.update_layout(title="File Types")
            st.plotly_chart(fig_types, use_container_width=True)
        
        with col2:
            df_files = pd.DataFrame([
                {'File': k, 'Chunks': v['chunks']}
                for k, v in files_info.items()
            ]).sort_values('Chunks', ascending=False).head(10)
            
            fig_chunks = px.bar(df_files, x='File', y='Chunks', title='Top Files')
            st.plotly_chart(fig_chunks, use_container_width=True)
        
        st.divider()
        
        df_inventory = pd.DataFrame([
            {
                'Filename': k,
                'Chunks': v['chunks'],
                'Type': v['type'],
                'Date': v['date']
            }
            for k, v in files_info.items()
        ])
        
        st.dataframe(df_inventory, use_container_width=True)
    else:
        st.info("📭 No documents yet!")

# Footer
st.divider()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 Docs", collection.count())
with col2:
    st.metric("💬 Messages", len(st.session_state.messages))
with col3:
    st.metric("🎯 Processed", st.session_state.performance_stats['total_files_processed'])
with col4:
    st.metric("📊 Queries", st.session_state.performance_stats['total_queries'])

st.caption("🚀 PAiKA Complete • Production-Ready RAG • Built with ❤️")