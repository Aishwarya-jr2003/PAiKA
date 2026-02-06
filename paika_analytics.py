import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import json

load_dotenv()

st.set_page_config(
    page_title="PAiKA Analytics",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    .stat-highlight {
        font-size: 2.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
if 'chroma_client' not in st.session_state:
    st.session_state.chroma_client = chromadb.PersistentClient(path="./paika_analytics_db")

if 'collection' not in st.session_state:
    try:
        st.session_state.collection = st.session_state.chroma_client.get_collection("paika_analytics")
    except:
        st.session_state.collection = st.session_state.chroma_client.create_collection("paika_analytics")

if 'groq_client' not in st.session_state:
    st.session_state.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

if 'usage_log' not in st.session_state:
    st.session_state.usage_log = []

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Load usage log from file if exists
def load_usage_log():
    try:
        with open('./usage_log.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_usage_log():
    with open('./usage_log.json', 'w') as f:
        json.dump(st.session_state.usage_log, f)

st.session_state.usage_log = load_usage_log()

# Header
st.title("📊 PAiKA Analytics Dashboard")
st.caption("Comprehensive insights into your knowledge base")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📚 Documents", "🔍 Query Analysis", "💬 Chat"])

with tab1:
    st.subheader("System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_chunks = st.session_state.collection.count()
    total_queries = len(st.session_state.usage_log)
    
    # Calculate average response time
    avg_response = 0
    if st.session_state.usage_log:
        response_times = [q.get('response_time', 0) for q in st.session_state.usage_log]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
    
    # Calculate success rate
    successful = sum(1 for q in st.session_state.usage_log if q.get('success', False))
    success_rate = (successful / total_queries * 100) if total_queries > 0 else 0
    
    with col1:
        st.metric(
            "📄 Total Chunks",
            total_chunks,
            help="Number of text chunks in database"
        )
    
    with col2:
        st.metric(
            "💬 Total Queries",
            total_queries,
            help="Number of questions asked"
        )
    
    with col3:
        st.metric(
            "⚡ Avg Response",
            f"{avg_response:.2f}s",
            help="Average query response time"
        )
    
    with col4:
        st.metric(
            "✅ Success Rate",
            f"{success_rate:.1f}%",
            help="Percentage of successful queries"
        )
    
    st.divider()
    
    # Usage over time
    st.subheader("📈 Usage Trends")
    
    if st.session_state.usage_log:
        # Create dataframe from usage log
        df_usage = pd.DataFrame([
            {
                'timestamp': datetime.fromisoformat(q['timestamp']),
                'response_time': q.get('response_time', 0),
                'success': q.get('success', False)
            }
            for q in st.session_state.usage_log
        ])
        
        # Group by date
        df_usage['date'] = df_usage['timestamp'].dt.date
        daily_queries = df_usage.groupby('date').size().reset_index(name='queries')
        
        fig = px.line(
            daily_queries,
            x='date',
            y='queries',
            title='Queries Over Time',
            labels={'date': 'Date', 'queries': 'Number of Queries'}
        )
        fig.update_traces(line_color='#667eea', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
        
        # Response time distribution
        col1, col2 = st.columns(2)
        
        with col1:
            fig_time = px.histogram(
                df_usage,
                x='response_time',
                title='Response Time Distribution',
                labels={'response_time': 'Response Time (s)'}
            )
            fig_time.update_traces(marker_color='#764ba2')
            st.plotly_chart(fig_time, use_container_width=True)
        
        with col2:
            success_count = df_usage['success'].value_counts()
            fig_success = go.Figure(data=[go.Pie(
                labels=['Success', 'Failed'],
                values=[success_count.get(True, 0), success_count.get(False, 0)],
                hole=0.4,
                marker_colors=['#38ef7d', '#ff6b6b']
            )])
            fig_success.update_layout(title="Query Success Rate")
            st.plotly_chart(fig_success, use_container_width=True)
    else:
        st.info("📊 No usage data yet. Start asking questions to see analytics!")

with tab2:
    st.subheader("📚 Document Library Analytics")
    
    if total_chunks > 0:
        all_data = st.session_state.collection.get()
        
        # Group by file type and filename
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
            # Pie chart for file types
            fig_types = go.Figure(data=[go.Pie(
                labels=list(file_types.keys()),
                values=list(file_types.values()),
                hole=0.4
            )])
            fig_types.update_layout(title="Documents by Type")
            st.plotly_chart(fig_types, use_container_width=True)
        
        with col2:
            # Bar chart for chunks per file
            df_files = pd.DataFrame([
                {'Filename': k, 'Chunks': v['chunks']}
                for k, v in files_info.items()
            ]).sort_values('Chunks', ascending=False).head(10)
            
            fig_chunks = px.bar(
                df_files,
                x='Filename',
                y='Chunks',
                title='Top 10 Files by Chunk Count'
            )
            fig_chunks.update_traces(marker_color='#667eea')
            st.plotly_chart(fig_chunks, use_container_width=True)
        
        st.divider()
        
        # File list table
        st.subheader("Document Inventory")
        df_inventory = pd.DataFrame([
            {
                'Filename': k,
                'Chunks': v['chunks'],
                'Type': v['type'],
                'Upload Date': v['date']
            }
            for k, v in files_info.items()
        ]).sort_values('Upload Date', ascending=False)
        
        st.dataframe(df_inventory, use_container_width=True)
        
        # Export option
        csv = df_inventory.to_csv(index=False)
        st.download_button(
            "📥 Download Inventory (CSV)",
            csv,
            "document_inventory.csv",
            "text/csv"
        )
    else:
        st.info("📭 No documents uploaded yet!")

with tab3:
    st.subheader("🔍 Query Analysis")
    
    if st.session_state.usage_log:
        # Most common queries
        queries = [q['query'] for q in st.session_state.usage_log]
        query_counts = Counter(queries)
        
        st.write("**Most Frequent Queries:**")
        df_queries = pd.DataFrame([
            {'Query': k, 'Count': v}
            for k, v in query_counts.most_common(10)
        ])
        st.dataframe(df_queries, use_container_width=True)
        
        st.divider()
        
        # Query length analysis
        query_lengths = [len(q.split()) for q in queries]
        avg_length = sum(query_lengths) / len(query_lengths)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Query Length", f"{avg_length:.1f} words")
        with col2:
            st.metric("Longest Query", f"{max(query_lengths)} words")
        
        # Query length distribution
        fig_length = px.histogram(
            x=query_lengths,
            title='Query Length Distribution',
            labels={'x': 'Number of Words', 'y': 'Frequency'}
        )
        st.plotly_chart(fig_length, use_container_width=True)
        
        # Recent queries
        st.subheader("Recent Queries")
        recent = st.session_state.usage_log[-10:][::-1]
        for i, q in enumerate(recent, 1):
            with st.expander(f"{i}. {q['query'][:50]}..."):
                st.write(f"**Time:** {q['timestamp']}")
                st.write(f"**Response Time:** {q.get('response_time', 0):.2f}s")
                st.write(f"**Success:** {'✅' if q.get('success', False) else '❌'}")
    else:
        st.info("📊 No query data yet!")

with tab4:
    st.subheader("💬 Interactive Chat")
    
    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
    
    # Chat input
    if prompt := st.chat_input("Ask anything about your documents..."):
        start_time = datetime.now()
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            if total_chunks == 0:
                answer = "📭 Please upload documents first!"
                success = False
            else:
                with st.spinner("🔍 Searching..."):
                    results = st.session_state.collection.query(
                        query_texts=[prompt],
                        n_results=min(3, total_chunks)
                    )
                    
                    if results['documents'][0]:
                        context = "\n\n".join(results['documents'][0])
                        
                        try:
                            response = st.session_state.groq_client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{
                                    "role": "user",
                                    "content": f"Based on:\n{context}\n\nQuestion: {prompt}\n\nProvide a helpful answer:"
                                }],
                                max_tokens=1000,
                                temperature=0.7
                            )
                            answer = response.choices[0].message.content
                            success = True
                        except Exception as e:
                            answer = f"❌ Error: {str(e)}"
                            success = False
                    else:
                        answer = "No relevant information found."
                        success = False
            
            st.markdown(answer)
        
        # Save message
        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Log usage
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        st.session_state.usage_log.append({
            'timestamp': start_time.isoformat(),
            'query': prompt,
            'response_time': response_time,
            'success': success
        })
        save_usage_log()
        
        st.rerun()

# Sidebar
with st.sidebar:
    st.title("⚙️ Quick Actions")
    
    # File upload
    st.subheader("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['txt', 'md', 'pdf', 'docx'],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("📤 Upload", type="primary"):
        for file in uploaded_files:
            try:
                content = file.read().decode('utf-8')
                st.session_state.collection.add(
                    documents=[content],
                    ids=[f"{file.name}_{datetime.now().timestamp()}"],
                    metadatas=[{
                        "filename": file.name,
                        "file_type": "txt",
                        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }]
                )
                st.success(f"✅ {file.name}")
            except Exception as e:
                st.error(f"❌ {file.name}: {str(e)}")
        st.rerun()
    
    st.divider()
    
    # Clear options
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("📊 Reset Analytics"):
        st.session_state.usage_log = []
        save_usage_log()
        st.rerun()
    
    if st.button("💾 Export All Data"):
        export_data = {
            'total_chunks': total_chunks,
            'total_queries': total_queries,
            'usage_log': st.session_state.usage_log
        }
        st.download_button(
            "Download JSON",
            json.dumps(export_data, indent=2),
            "paika_analytics.json",
            "application/json"
        )

# Footer
st.divider()
st.caption("📊 PAiKA Analytics • Built with Streamlit • Powered by Groq & ChromaDB")