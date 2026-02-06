import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
import traceback
import logging
import json

# Set up logging
logging.basicConfig(
    filename='paika.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Page config
st.set_page_config(
    page_title="PAiKA Robust",
    page_icon="🛡️",
    layout="wide"
)

# ==================== PART 4: USAGE LOGGING FUNCTION ====================
def log_query(query, response_time, success=True):
    """Log user queries to file for analytics"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'response_time': response_time,
        'success': success
    }
    
    # Add to session state
    if 'usage_log' not in st.session_state:
        st.session_state.usage_log = []
    st.session_state.usage_log.append(log_entry)
    
    # Save to file
    try:
        with open('paika_usage.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        logger.info(f"Query logged: {query[:50]}... (Success: {success}, Time: {response_time:.2f}s)")
    except Exception as e:
        logger.error(f"Failed to log query: {str(e)}")
# ========================================================================

# Error handling decorator
def handle_errors(func):
    """Decorator for graceful error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            st.error(f"❌ An error occurred: {str(e)}")
            st.expander("🔍 Error Details").code(traceback.format_exc())
            return None
    return wrapper

# Safe initialization
def safe_init():
    """Initialize with proper error handling"""
    try:
        if 'chroma_client' not in st.session_state:
            st.session_state.chroma_client = chromadb.PersistentClient(path="./paika_shared_db")
        
        if 'collection' not in st.session_state:
            try:
                st.session_state.collection = st.session_state.chroma_client.get_collection("paika_data")
            except:
                st.session_state.collection = st.session_state.chroma_client.create_collection("paika_data")
        
        if 'groq_client' not in st.session_state:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                st.error("❌ GROQ_API_KEY not found in environment variables!")
                st.info("💡 Please add your API key to the .env file")
                st.stop()
            st.session_state.groq_client = Groq(api_key=api_key)
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # PART 4: Initialize usage log
        if 'usage_log' not in st.session_state:
            st.session_state.usage_log = []
        
        return True
    
    except Exception as e:
        st.error(f"❌ Initialization failed: {str(e)}")
        with st.expander("🔍 Debug Info"):
            st.code(traceback.format_exc())
        return False

# Initialize
if not safe_init():
    st.stop()

# Header
st.title("🛡️ PAiKA Robust Edition")
st.caption("Production-ready with comprehensive error handling & analytics")

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Health check
    st.subheader("💚 System Health")
    
    health_checks = {
        "ChromaDB": st.session_state.get('chroma_client') is not None,
        "Collection": st.session_state.get('collection') is not None,
        "Groq API": st.session_state.get('groq_client') is not None,
    }
    
    for service, status in health_checks.items():
        if status:
            st.success(f"✅ {service}")
        else:
            st.error(f"❌ {service}")
    
    st.divider()
    
    # PART 4: Show session statistics
    st.subheader("📊 Session Stats")
    st.metric("💬 Queries This Session", len(st.session_state.usage_log))
    st.metric("📝 Messages", len(st.session_state.messages))
    st.metric("📄 Documents", st.session_state.collection.count())
    
    st.divider()
    
    # Safe file upload
    st.subheader("📁 Upload")
    uploaded_files = st.file_uploader("Choose files", type=['txt'], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Process", type="primary"):
            success_count = 0
            error_count = 0
            
            for file in uploaded_files:
                try:
                    content = file.read().decode('utf-8')
                    
                    # Validate content
                    if len(content.strip()) == 0:
                        st.warning(f"⚠️ {file.name} is empty")
                        continue
                    
                    # Add to collection
                    st.session_state.collection.add(
                        documents=[content],
                        ids=[f"{file.name}_{datetime.now().timestamp()}"],
                        metadatas=[{
                            "filename": file.name,
                            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "file_type": ".txt"
                        }]
                    )
                    
                    success_count += 1
                    st.success(f"✅ {file.name}")
                    logger.info(f"File uploaded: {file.name}")
                
                except UnicodeDecodeError:
                    st.error(f"❌ {file.name}: Invalid encoding")
                    error_count += 1
                    logger.error(f"Encoding error: {file.name}")
                except Exception as e:
                    st.error(f"❌ {file.name}: {str(e)}")
                    error_count += 1
                    logger.error(f"Upload error: {file.name} - {str(e)}")
            
            # Summary
            if success_count > 0:
                st.balloons()
            st.info(f"✅ {success_count} succeeded | ❌ {error_count} failed")
    
    st.divider()
    
    # Actions
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("📊 View Analytics"):
        st.info("Run: streamlit run paika_analytics.py --server.port 8502")

# Chat with error handling
st.subheader("💬 Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

if prompt := st.chat_input("Ask..."):
    # PART 4: Start timing the query
    start_time = datetime.now()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            if st.session_state.collection.count() == 0:
                answer = "📭 No documents uploaded yet!"
                st.markdown(answer)
                
                # PART 4: Log failed query (no documents)
                response_time = (datetime.now() - start_time).total_seconds()
                log_query(prompt, response_time, success=False)
                
            else:
                # Safe search
                results = st.session_state.collection.query(
                    query_texts=[prompt],
                    n_results=min(3, st.session_state.collection.count())
                )
                
                if results and results['documents'] and results['documents'][0]:
                    context = "\n\n".join(results['documents'][0])
                    
                    # Safe API call with timeout handling
                    try:
                        response = st.session_state.groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": f"Based on: {context}\n\nQ: {prompt}\n\nA:"}],
                            max_tokens=1000,
                            temperature=0.7
                        )
                        answer = response.choices[0].message.content
                        st.markdown(answer)
                        
                        # PART 4: Log successful query
                        response_time = (datetime.now() - start_time).total_seconds()
                        log_query(prompt, response_time, success=True)
                        
                    except Exception as api_error:
                        st.error(f"API Error: {str(api_error)}")
                        answer = "Sorry, I encountered an error generating a response."
                        
                        # PART 4: Log API error
                        response_time = (datetime.now() - start_time).total_seconds()
                        log_query(prompt, response_time, success=False)
                        logger.error(f"API error: {str(api_error)}")
                else:
                    answer = "No relevant information found."
                    st.markdown(answer)
                    
                    # PART 4: Log query with no results
                    response_time = (datetime.now() - start_time).total_seconds()
                    log_query(prompt, response_time, success=False)
        
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            st.error(f"❌ Error: {str(e)}")
            answer = "An error occurred."
            
            # PART 4: Log general error
            response_time = (datetime.now() - start_time).total_seconds()
            log_query(prompt, response_time, success=False)
    
    st.session_state.messages.append({"role": "assistant", "content": answer})

# Footer
st.divider()
st.markdown("🛡️ PAiKA Robust Edition - Day 13 Complete with Analytics Integration")