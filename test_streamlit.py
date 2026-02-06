import streamlit as st

# Page config (must be first)
st.set_page_config(
    page_title="Streamlit Test",
    page_icon="🚀",
    layout="wide"
)

# Title
st.title("🚀 Streamlit Basics Test")

# Text
st.write("Welcome to Streamlit!")

# Headers
st.header("📝 Text Elements")
st.subheader("Different text types:")
st.text("Plain text")
st.markdown("**Bold** and *italic* markdown")
st.code("print('Hello World!')", language='python')

# Input widgets
st.header("🎛️ Input Widgets")

name = st.text_input("Enter your name:")
if name:
    st.success(f"Hello, {name}! 👋")

number = st.slider("Pick a number:", 0, 100, 50)
st.info(f"You selected: {number}")

# Buttons
st.header("🔘 Buttons")
if st.button("Click me!"):
    st.balloons()
    st.success("You clicked the button! 🎉")

# Columns
st.header("📐 Layout")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Metric 1", "100", "10%")

with col2:
    st.metric("Metric 2", "200", "-5%")

with col3:
    st.metric("Metric 3", "300", "15%")

# Sidebar
st.sidebar.title("⚙️ Sidebar")
st.sidebar.write("This is the sidebar")
option = st.sidebar.selectbox("Choose:", ["Option 1", "Option 2", "Option 3"])
st.sidebar.success(f"Selected: {option}")

# Chat messages
st.header("💬 Chat Interface")

with st.chat_message("user"):
    st.write("Hello!")

with st.chat_message("assistant"):
    st.write("Hi there! How can I help?")

# Expander
with st.expander("📦 Click to expand"):
    st.write("Hidden content here!")
    st.image("https://via.placeholder.com/300x150", caption="Sample image")

# Status
st.header("📊 Status Elements")
st.success("Success message!")
st.info("Info message")
st.warning("Warning message")
st.error("Error message")

# Progress
st.header("⏳ Progress")
import time

progress_bar = st.progress(0)
for i in range(100):
    progress_bar.progress(i + 1)
    time.sleep(0.01)

st.success("Complete!")

# File upload
st.header("📁 File Upload")
uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'csv'])
if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")