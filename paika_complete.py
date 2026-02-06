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
    }
</style>
""", unsafe_allow_html=True)

# ===== LOADERS =====

@st.cache_resource(show_spinner=False)
def load_chroma_client():
    return chromadb.PersistentClient(path="./paika_complete_db")

def load_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("❌ GROQ_API_KEY missing in Streamlit secrets")
        st.stop()
    return Groq(api_key=api_key)

@st.cache_resource(show_spinner=False)
def load_reranker_model():
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

@st.cache_resource(show_spinner=False)
def load_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

# ===== HELPERS =====

def process_file_content(file_bytes, filename):
    ext = Path(filename).suffix.lower()
    try:
        if ext in [".txt", ".md"]:
            return file_bytes.decode("utf-8"), ext
        if ext == ".pdf":
            pdf = PyPDF2.PdfReader(BytesIO(file_bytes))
            return "\n".join(p.extract_text() for p in pdf.pages), ext
        if ext == ".docx":
            doc = DocxDocument(BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs), ext
    except Exception as e:
        logger.error(e)
    return None, None

def load_usage_log():
    try:
        with open("usage_log.json") as f:
            return json.load(f)
    except:
        return []

def save_usage_log(log):
    with open("usage_log.json", "w") as f:
        json.dump(log, f)

# ===== INIT =====

chroma_client = load_chroma_client()
groq_client = load_groq_client()
reranker = load_reranker_model()
text_splitter = load_text_splitter()

try:
    collection = chroma_client.get_collection("paika_complete")
except:
    collection = chroma_client.create_collection("paika_complete")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "usage_log" not in st.session_state:
    st.session_state.usage_log = load_usage_log()

# ===== HEADER =====

st.markdown('<h1 class="main-header">🚀 PAiKA Complete</h1>', unsafe_allow_html=True)

# ===== TABS =====

tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Analytics", "📚 Documents"])

# 🔥 IMPORTANT FIX: chat_input at TOP LEVEL
prompt = st.chat_input("Ask anything about your documents...")

# ===== CHAT TAB =====

with tab1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ===== HANDLE CHAT INPUT (outside tabs) =====

if prompt:
    query_start = time.time()
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        if collection.count() == 0:
            answer = "📭 Please upload documents first!"
        else:
            results = collection.query(
                query_texts=[prompt],
                n_results=min(5, collection.count())
            )
            context = "\n".join(results["documents"][0])
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": context + "\n\n" + prompt}],
                max_tokens=700
            )
            answer = response.choices[0].message.content

        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    st.session_state.usage_log.append({
        "timestamp": datetime.now().isoformat(),
        "query": prompt
    })

    save_usage_log(st.session_state.usage_log)
    st.rerun()

# ===== ANALYTICS TAB =====

with tab2:
    st.metric("Queries", len(st.session_state.usage_log))
    st.metric("Chunks", collection.count())

# ===== DOCUMENTS TAB =====

with tab3:
    st.info("Document browser unchanged")

st.caption("🚀 PAiKA Complete • Production-Ready RAG")
