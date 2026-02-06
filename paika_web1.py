import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
import numpy as np

# Page config (MUST be first Streamlit command)
st.set_page_config(
    page_title="PAiKA - AI Knowledge Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment
load_dotenv()

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
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
    .document-card {
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'messages': [],
        'documents_loaded': False,
        'collection': None,
        'bm25_index': None,
        'doc_ids': [],
        'total_chunks': 0,
        'search_weight': 0.5
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Title
st.markdown('<p class="main-header">🧠 PAiKA</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your Personal AI Knowledge Assistant</p>', unsafe_allow_html=True)

st.divider()

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # API Status
    if os.getenv("GROQ_API_KEY"):
        st.success("✅ API Connected")
    else:
        st.error("❌ API Key Missing")
    
    st.divider()
    
    # Search Settings
    st.subheader("Search Configuration")
    st.session_state.search_weight = st.slider(
        "Semantic vs Keyword",
        0.0, 1.0, 0.5,
        help="0 = Keyword only, 1 = Semantic only, 0.5 = Hybrid"
    )
    
    st.divider()
    
    # Document Stats
    st.subheader("📊 Statistics")
    st.metric("Documents Loaded", "Yes" if st.session_state.documents_loaded else "No")
    st.metric("Total Chunks", st.session_state.total_chunks)
    
    st.divider()
    
    # Clear chat
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main content area
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📁 Documents", "🔍 Search"])

with tab1:
    st.subheader("Chat with Your Knowledge Base")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response (placeholder for now)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # This will be replaced with actual search
                response = f"🔍 Searching for: '{prompt}'\n\n(Connect to backend in next step)"
                st.write(response)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

with tab2:
    st.subheader("Document Management")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=['txt', 'pdf', 'docx', 'eml', 'csv', 'html', 'md'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"📎 {len(uploaded_files)} files selected")
        
        # Show file list
        for file in uploaded_files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {file.name}")
            with col2:
                st.write(f"{file.size} bytes")
        
        # Process button
        if st.button("🚀 Process Documents"):
            with st.spinner("Processing..."):
                # This will be implemented next
                st.success("Processing complete! (Implementation in next step)")
                st.session_state.documents_loaded = True

with tab3:
    st.subheader("Advanced Search")
    
    search_query = st.text_input("Search query")
    
    if st.button("Search"):
        if search_query:
            st.info(f"Searching for: {search_query}")
            st.info(f"Using semantic weight: {st.session_state.search_weight}")
            # Results will appear here
        else:
            st.warning("Please enter a search query")

# Footer
st.divider()
st.caption("PAiKA v1.0 | Built with Streamlit + ChromaDB + Groq")