import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from datetime import datetime
import json


load_dotenv()

# Page config with theme
st.set_page_config(
    page_title="PAiKA - Export Edition",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme toggle
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Dynamic CSS based on theme
if st.session_state.dark_mode:
    st.markdown("""
    <style>
        .main { background-color: #1e1e1e; color: #ffffff; }
        .stTextInput>div>div>input { background-color: #2d2d2d; color: #ffffff; }
        .source-card { background-color: #2d2d2d; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .main { background-color: #ffffff; color: #000000; }
        .source-card { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'chroma_client' not in st.session_state:
    st.session_state.chroma_client = chromadb.PersistentClient(path="./paika_export_db")

if 'collection' not in st.session_state:
    try:
        st.session_state.collection = st.session_state.chroma_client.get_collection("paika_export")
    except:
        st.session_state.collection = st.session_state.chroma_client.create_collection("paika_export")

if 'groq_client' not in st.session_state:
    st.session_state.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🤖 PAiKA Export Edition")

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")

    # Theme toggle
    st.session_state.dark_mode = st.toggle(
        "🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode",
        value=st.session_state.dark_mode
    )

    if st.session_state.dark_mode != st.session_state.get('prev_dark_mode', False):
        st.session_state.prev_dark_mode = st.session_state.dark_mode
        st.rerun()

    st.divider()

    # Export options
    st.subheader("📥 Export Chat")

    if st.session_state.messages:
        export_format = st.selectbox("Format", ["JSON", "Markdown", "Text"])

        if st.button("📥 Download Chat", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if export_format == "JSON":
                data = json.dumps(st.session_state.messages, indent=2)
                st.download_button(
                    "💾 Save JSON",
                    data,
                    f"paika_chat_{timestamp}.json",
                    "application/json",
                    use_container_width=True
                )

            elif export_format == "Markdown":
                md_content = f"# PAiKA Chat Export\n\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"
                for msg in st.session_state.messages:
                    role = "**User:**" if msg['role'] == 'user' else "**PAiKA:**"
                    md_content += f"{role}\n\n{msg['content']}\n\n---\n\n"

                st.download_button(
                    "💾 Save Markdown",
                    md_content,
                    f"paika_chat_{timestamp}.md",
                    "text/markdown",
                    use_container_width=True
                )

            else:
                txt_content = f"PAiKA Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                txt_content += "=" * 60 + "\n\n"
                for msg in st.session_state.messages:
                    role = "USER:" if msg['role'] == 'user' else "PAiKA:"
                    txt_content += f"{role}\n{msg['content']}\n\n{'-' * 60}\n\n"

                st.download_button(
                    "💾 Save Text",
                    txt_content,
                    f"paika_chat_{timestamp}.txt",
                    "text/plain",
                    use_container_width=True
                )
    else:
        st.info("No chat history yet!")

    st.divider()

    # Stats
    st.subheader("📊 Session Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Documents", st.session_state.collection.count())

    if st.session_state.messages:
        user_msgs = len([m for m in st.session_state.messages if m['role'] == 'user'])
        st.metric("Questions", user_msgs)

# Main chat
st.subheader("💬 Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = f"This is a demo response to: {prompt}\n\nExport features are working!"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

# Footer
st.divider()
st.caption("🚀 PAiKA with Export & Theme Support")
