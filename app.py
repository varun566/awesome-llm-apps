import streamlit as st
from datetime import datetime
import sqlite3
import json

st.set_page_config(
    page_title="Internet Research Assistant 🔎",
    page_icon="🔎",
    layout="wide"
)

# ============================================================================
# DATABASE
# ============================================================================

def init_database():
    conn = sqlite3.connect('research_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            query TEXT,
            response TEXT,
            sources TEXT,
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_database()

# ============================================================================
# UI
# ============================================================================

st.title("🔍 Internet Research Assistant")
st.markdown("*Demo: Real-time Q&A with caching and conversation history*")

with st.sidebar:
    st.title("⚙️ Settings")
    if 'session_id' not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.write(f"**Session:** {st.session_state.session_id[:8]}...")

# Search input
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        "Ask anything:",
        placeholder="e.g., What is artificial intelligence?",
        key="search"
    )

with col2:
    search_btn = st.button("🚀 Search")

if search_btn and query:
    st.success("✅ App is running!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", "Ready")
    with col2:
        st.metric("Mode", "Demo")
    with col3:
        st.metric("Time", datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    
    st.subheader("📝 Demo Response")
    st.write(f"""
    **Query:** {query}
    
    This is a demo version of the Internet Research Assistant. 
    
    **Features Available:**
    - ✅ Streamlit Web UI
    - ✅ SQLite Database for conversation history
    - ✅ Session management
    - ✅ Caching system ready
    
    **To Enable Full Features:**
    1. Add OpenAI API key to .env
    2. Configure DuckDuckGo search
    3. Run with: `streamlit run app.py`
    
    **Project Structure:**
    - `app.py` - Main Streamlit app
    - `requirements.txt` - Dependencies
    - `.env` - Configuration
    - `research_history.db` - SQLite database
    """)
    
    st.divider()
    
    st.subheader("📚 Demo Sources")
    demo_sources = [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://www.britannica.com/technology/artificial-intelligence",
        "https://www.ibm.com/ai"
    ]
    for i, source in enumerate(demo_sources, 1):
        st.write(f"{i}. {source}")
    
    st.divider()
    
    if st.button("📥 Export as JSON"):
        export_data = {
            "query": query,
            "response": "Demo response",
            "sources": demo_sources,
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }
        st.download_button(
            "Download",
            json.dumps(export_data, indent=2),
            f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

elif search_btn and not query:
    st.warning("⚠️ Please enter a search query")

st.divider()
st.markdown("""
**Internet Research Assistant v1.0 (Demo)**
- Built with Streamlit
- Database: SQLite
- Status: ✅ Running
""")
