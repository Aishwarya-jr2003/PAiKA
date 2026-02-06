import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import numpy as np

# Import loaders
import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
import csv
from bs4 import BeautifulSoup

load_dotenv()

# Page config
st.set_page_config(
    page_title="PAiKA Pro - AI Knowledge Assistant",
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
        margin-bottom: 0;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-top: -1rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    
    .source-card {
        background-color: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    
    .score-badge {
        background-color: #28a745;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Document loader
class UniversalLoader:
    @staticmethod
    def load_text(file):
        return file.read().decode('utf-8')
    
    @staticmethod
    def load_pdf(file):
        try:
            from io import BytesIO
            pdf = PyPDF2.PdfReader(BytesIO(file.read()))
            return "\n".join([page.extract_text() for page in pdf.pages])
        except:
            return None
    
    @staticmethod
    def load_docx(file):
        from io import BytesIO
        doc = DocxDocument(BytesIO(file.read()))
        return "\n".join([p.text for p in doc.paragraphs])
    
    @staticmethod
    def load_csv(file):
        import io
        content = file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames
        rows = [f"Row {i}: " + ", ".join([f"{k}={v}" for k, v in row.items() if v])
                for i, row in enumerate(reader, 1)]
        return f"CSV Data\nColumns: {', '.join(headers)}\n\n" + "\n".join(rows)
    
    @staticmethod
    def load_html(file):
        soup = BeautifulSoup(file.read(), 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()
    
    @classmethod
    def load(cls, file):
        ext = Path(file.name).suffix.lower()
        loaders = {
            '.txt': cls.load_text,
            '.pdf': cls.load_pdf,
            '.docx': cls.load_docx,
            '.csv': cls.load_csv,
            '.html': cls.load_html,
        }
        if ext in loaders:
            return loaders[ext](file), ext
        return None, None

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'chroma_client' not in st.session_state:
    st.session_state.chroma_client = chromadb.PersistentClient(path="./paika_pro_db")

if 'collection' not in st.session_state:
    try:
        st.session_state.collection = st.session_state.chroma_client.get_collection("paika_pro")
    except:
        st.session_state.collection = st.session_state.chroma_client.create_collection("paika_pro")

if 'groq_client' not in st.session_state:
    st.session_state.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

if 'text_splitter' not in st.session_state:
    st.session_state.text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

if 'reranker' not in st.session_state:
    with st.spinner("Loading re-ranker model..."):
        st.session_state.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Header
st.markdown('<h1 class="main-header">🤖 PAiKA Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Professional AI Knowledge Assistant with Advanced RAG</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # Stats
    st.subheader("📊 Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Chunks", st.session_state.collection.count())
    with col2:
        st.metric("💬 Turns", len(st.session_state.messages) // 2)
    
    st.divider()
    
    # Upload section
    st.subheader("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['txt', 'pdf', 'docx', 'csv', 'html'],
        accept_multiple_files=True,
        help="Supports: TXT, PDF, DOCX, CSV, HTML"
    )
    
    if uploaded_files:
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status = st.empty()
            
            for i, file in enumerate(uploaded_files):
                status.text(f"Processing {file.name}...")
                
                try:
                    # Load content
                    content, file_type = UniversalLoader.load(file)
                    
                    if content:
                        # Chunk
                        chunks = st.session_state.text_splitter.split_text(content)
                        
                        # Add to collection
                        chunk_ids = [f"{file.name}_chunk_{j}" for j in range(len(chunks))]
                        metadatas = [{
                            "filename": file.name,
                            "file_type": file_type,
                            "chunk_index": j,
                            "upload_date": str(datetime.now())
                        } for j in range(len(chunks))]
                        
                        st.session_state.collection.add(
                            documents=chunks,
                            ids=chunk_ids,
                            metadatas=metadatas
                        )
                        
                        st.success(f"✅ {file.name} ({len(chunks)} chunks)")
                    else:
                        st.error(f"❌ {file.name}: Failed to load")
                
                except Exception as e:
                    st.error(f"❌ {file.name}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status.success("✅ All files processed!")
            st.rerun()
    
    st.divider()
    
    # Search settings
    st.subheader("🔍 Search Settings")
    search_mode = st.selectbox(
        "Search Mode",
        ["Hybrid + Re-rank", "Semantic Only", "Keyword Only"],
        help="Hybrid + Re-rank gives best results"
    )
    
    n_results = st.slider("Results to show", 1, 10, 5)
    
    st.divider()
    
    # Actions
    st.subheader("🛠️ Actions")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("⚠️ Reset Database", use_container_width=True):
        if st.checkbox("Confirm reset"):
            st.session_state.chroma_client.delete_collection("paika_pro")
            st.session_state.collection = st.session_state.chroma_client.create_collection("paika_pro")
            st.session_state.messages = []
            st.success("Reset!")
            st.rerun()

# Main area tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📚 Documents", "📈 Analytics"])

with tab1:
    # Chat interface
    st.subheader("Chat with your knowledge base")
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            if "sources" in message and message["sources"]:
                with st.expander(f"📚 {len(message['sources'])} Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        st.markdown(f"""
                        <div class="source-card">
                            <b>{i}. {source['filename']}</b> 
                            <span class="score-badge">{source['score']:.2%}</span>
                            <br><small>{source['snippet'][:150]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Ask anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if st.session_state.collection.count() == 0:
                answer = "📭 No documents loaded yet. Please upload some documents first!"
                sources = []
            else:
                with st.spinner("🔍 Searching and analyzing..."):
                    # Search
                    results = st.session_state.collection.query(
                        query_texts=[prompt],
                        n_results=min(20, st.session_state.collection.count())
                    )
                    
                    if results['documents'][0]:
                        # Re-rank
                        candidates = []
                        for doc, metadata, distance in zip(
                            results['documents'][0],
                            results['metadatas'][0],
                            results['distances'][0]
                        ):
                            candidates.append({
                                'content': doc,
                                'metadata': metadata,
                                'semantic_score': 1 - distance
                            })
                        
                        # Cross-encoder re-ranking
                        pairs = [(prompt, c['content']) for c in candidates]
                        rerank_scores = st.session_state.reranker.predict(pairs)
                        
                        for cand, score in zip(candidates, rerank_scores):
                            cand['rerank_score'] = float(score)
                        
                        # Sort and take top N
                        candidates.sort(key=lambda x: x['rerank_score'], reverse=True)
                        top_results = candidates[:n_results]
                        
                        # Build context
                        context = ""
                        sources = []
                        
                        for i, result in enumerate(top_results, 1):
                            context += f"\n\n[{i}] {result['metadata']['filename']}\n{result['content']}"
                            sources.append({
                                'filename': result['metadata']['filename'],
                                'score': result['rerank_score'],
                                'snippet': result['content']
                            })
                        
                        # Generate answer
                        prompt_text = f"""Based on these sources:
{context}

Question: {prompt}

Provide a comprehensive answer. Reference sources using [1], [2], etc.

Answer:"""
                        
                        response = st.session_state.groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt_text}],
                            max_tokens=1500
                        )
                        
                        answer = response.choices[0].message.content
                    else:
                        answer = "No relevant documents found."
                        sources = []
            
            st.markdown(answer)
            
            if sources:
                with st.expander(f"📚 {len(sources)} Sources"):
                    for i, source in enumerate(sources, 1):
                        st.markdown(f"""
                        <div class="source-card">
                            <b>{i}. {source['filename']}</b> 
                            <span class="score-badge">{source['score']:.2%}</span>
                            <br><small>{source['snippet'][:150]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

with tab2:
    # Document browser
    st.subheader("📚 Document Library")
    
    if st.session_state.collection.count() > 0:
        all_data = st.session_state.collection.get()
        
        # Group by filename
        files = {}
        for metadata in all_data['metadatas']:
            filename = metadata['filename']
            if filename not in files:
                files[filename] = []
            files[filename].append(metadata)
        
        st.metric("Total Files", len(files))
        
        for filename, chunks in files.items():
            with st.expander(f"📄 {filename} ({len(chunks)} chunks)"):
                st.write(f"**File type:** {chunks[0]['file_type']}")
                st.write(f"**Uploaded:** {chunks[0]['upload_date']}")
                st.write(f"**Chunks:** {len(chunks)}")
    else:
        st.info("No documents yet. Upload some files!")

with tab3:
    # Analytics
    st.subheader("📈 Usage Analytics")
    
    if st.session_state.messages:
        st.metric("Total Questions", len([m for m in st.session_state.messages if m['role'] == 'user']))
        st.metric("Total Answers", len([m for m in st.session_state.messages if m['role'] == 'assistant']))
        
        # Recent queries
        st.subheader("Recent Queries")
        recent = [m['content'] for m in st.session_state.messages if m['role'] == 'user'][-5:]
        for i, q in enumerate(reversed(recent), 1):
            st.text(f"{i}. {q}")
    else:
        st.info("No activity yet. Start chatting!")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p><b>PAiKA Pro v1.0</b> - Advanced RAG System</p>
    <p>🚀 Hybrid Search • 🎯 Re-Ranking • 💾 ChromaDB • 🤖 Groq AI</p>
</div>
""", unsafe_allow_html=True)