"""
Internet Research Assistant
===========================
A production-ready multi-agent research assistant that combines:
- Real-time web search (DuckDuckGo)
- Research analysis and verification (OpenAI)
- Streaming response synthesis
- Conversation persistence (SQLite)
- Smart TTL caching
"""

import os
import sys
import time
import uuid

import streamlit as st
from openai import OpenAI

# Ensure the project root is on sys.path so sub-modules resolve correctly.
sys.path.insert(0, os.path.dirname(__file__))

from agents.web_search_agent import search_web, multi_search
from agents.research_agent import research_and_verify, generate_related_questions
from agents.writer_agent import write_response_stream
from config.settings import Settings
from ui.components import (
    load_css,
    render_confidence_badge,
    render_sources,
    render_related_questions,
    render_cache_stats,
    render_analytics_chart,
    export_conversation,
)
from utils.cache import TTLCache
from utils.database import Database
from utils.helpers import make_cache_key, score_confidence, generate_session_id
from utils.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Internet Research Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()

# ──────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ──────────────────────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = generate_session_id()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "settings" not in st.session_state:
    st.session_state.settings = Settings()
if "cache" not in st.session_state:
    st.session_state.cache = TTLCache(
        max_size=st.session_state.settings.cache_max_size,
        default_ttl=st.session_state.settings.cache_ttl_seconds,
    )
if "db" not in st.session_state:
    st.session_state.db = Database(st.session_state.settings.db_path)

settings: Settings = st.session_state.settings
cache: TTLCache = st.session_state.cache
db: Database = st.session_state.db

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    api_key_input = st.text_input(
        "OpenAI API Key",
        value=settings.openai_api_key,
        type="password",
        help="Your OpenAI API key. Also readable from the OPENAI_API_KEY env var.",
    )
    if api_key_input:
        settings.openai_api_key = api_key_input
        os.environ["OPENAI_API_KEY"] = api_key_input

    settings.openai_model = st.selectbox(
        "Model",
        ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"].index(
            settings.openai_model
        )
        if settings.openai_model in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        else 0,
    )

    settings.max_search_results = st.slider("Search results per query", 3, 10, settings.max_search_results)
    settings.max_concurrent_searches = st.slider("Concurrent searches", 1, 5, settings.max_concurrent_searches)

    st.divider()

    # Cache controls
    render_cache_stats(cache.stats())
    if st.button("🗑️ Clear cache", use_container_width=True):
        cache.clear()
        st.success("Cache cleared.")

    st.divider()

    # Session management
    st.markdown("### 💬 Session")
    st.code(st.session_state.session_id[:16] + "…", language=None)

    if st.button("🆕 New Session", use_container_width=True):
        st.session_state.session_id = generate_session_id()
        st.session_state.messages = []
        st.rerun()

    # Export conversation
    if st.session_state.messages:
        st.divider()
        fmt = st.radio("Export format", ["json", "text"], horizontal=True)
        export_data = export_conversation(st.session_state.messages, fmt=fmt)
        st.download_button(
            label="⬇️ Export Conversation",
            data=export_data,
            file_name=f"conversation_{st.session_state.session_id[:8]}.{fmt}",
            mime="application/json" if fmt == "json" else "text/plain",
            use_container_width=True,
        )

    st.divider()

    # Analytics
    with st.expander("📈 Search Analytics", expanded=False):
        analytics = db.get_analytics(limit=50)
        render_analytics_chart(analytics)
        st.caption(f"Total searches: {len(analytics)}")

    # Past sessions
    with st.expander("🕑 Past Sessions", expanded=False):
        sessions = db.list_sessions()
        if sessions:
            for s in sessions[:10]:
                sid = s["session_id"][:16]
                count = s["message_count"]
                if st.button(f"📂 {sid}… ({count} msgs)", key=f"sess_{s['session_id']}"):
                    history = db.get_conversation(s["session_id"])
                    st.session_state.session_id = s["session_id"]
                    st.session_state.messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in history
                    ]
                    st.rerun()
        else:
            st.caption("No past sessions.")

# ──────────────────────────────────────────────────────────────────────────────
# Main area
# ──────────────────────────────────────────────────────────────────────────────
st.title("🔍 Internet Research Assistant")
st.caption(
    "Ask any question — I'll search the web in real time, verify the information "
    "across multiple sources, and deliver a well-cited answer."
)

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🔍"):
        st.markdown(msg["content"])
        if msg.get("confidence") is not None:
            st.markdown(
                render_confidence_badge(msg["confidence"]),
                unsafe_allow_html=True,
            )
        if msg.get("sources"):
            render_sources(msg["sources"])


# ──────────────────────────────────────────────────────────────────────────────
# Related-question callback (sets a pending query so it runs on next rerun)
# ──────────────────────────────────────────────────────────────────────────────
def set_pending_query(q: str) -> None:
    st.session_state["_pending_query"] = q


# Show related questions from last assistant message
last_assistant = next(
    (m for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
    None,
)
if last_assistant and last_assistant.get("related_questions"):
    render_related_questions(last_assistant["related_questions"], set_pending_query)


# ──────────────────────────────────────────────────────────────────────────────
# Handle a pending query injected by a related-question button
# ──────────────────────────────────────────────────────────────────────────────
pending = st.session_state.pop("_pending_query", None)

# ──────────────────────────────────────────────────────────────────────────────
# Chat input
# ──────────────────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask a question…") or pending

if user_input:
    if not settings.openai_api_key:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        st.stop()

    # Display user message
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})
    db.save_message(st.session_state.session_id, "user", user_input)

    client = OpenAI(api_key=settings.openai_api_key)
    start_time = time.perf_counter()

    # ── Step 1: Web search ────────────────────────────────────────────────
    with st.status("🌐 Searching the web…", expanded=True) as status:
        # Build 2-3 query variants for broader coverage
        variant_queries = [user_input]
        if len(user_input.split()) > 3:
            variant_queries.append(f"{user_input} latest news")
            variant_queries.append(f"{user_input} explained")

        search_results_map = multi_search(
            variant_queries[: settings.max_concurrent_searches],
            max_results=settings.max_search_results,
            cache=cache,
            db=db,
            max_workers=settings.max_concurrent_searches,
        )
        combined_results = "\n\n---\n\n".join(search_results_map.values())
        status.update(label="✅ Web search complete", state="complete", expanded=False)

    # ── Step 2: Research & verify ─────────────────────────────────────────
    with st.status("🔬 Analysing and verifying…", expanded=True) as status:
        research = research_and_verify(
            user_input,
            combined_results,
            client=client,
            model=settings.openai_model,
        )
        status.update(label="✅ Analysis complete", state="complete", expanded=False)

    # ── Step 3: Stream the final answer ───────────────────────────────────
    with st.chat_message("assistant", avatar="🔍"):
        answer_placeholder = st.empty()
        full_answer = ""
        for token in write_response_stream(
            user_input,
            research["analysis"],
            combined_results,
            client=client,
            model=settings.openai_model,
        ):
            full_answer += token
            answer_placeholder.markdown(full_answer + "▌")
        answer_placeholder.markdown(full_answer)

    elapsed = time.perf_counter() - start_time

    # ── Confidence + sources ──────────────────────────────────────────────
    raw_sources = []
    for results_text in search_results_map.values():
        # Reconstruct minimal source dicts from formatted text (best-effort)
        for line in results_text.split("\n"):
            if line.startswith("**URL:**"):
                raw_sources.append({"url": line.replace("**URL:**", "").strip()})

    confidence = score_confidence(raw_sources, full_answer)
    st.markdown(render_confidence_badge(confidence), unsafe_allow_html=True)

    # ── Related questions ─────────────────────────────────────────────────
    related = generate_related_questions(
        user_input,
        full_answer,
        client=client,
        model=settings.openai_model,
    )

    # Persist assistant message
    assistant_msg = {
        "role": "assistant",
        "content": full_answer,
        "confidence": confidence,
        "sources": raw_sources,
        "related_questions": related,
        "processing_time": elapsed,
    }
    st.session_state.messages.append(assistant_msg)
    db.save_message(
        st.session_state.session_id,
        "assistant",
        full_answer,
        metadata={"confidence": confidence, "processing_time": elapsed},
    )
    db.log_search(
        session_id=st.session_state.session_id,
        query=user_input,
        sources=len(raw_sources),
        cached=False,
        duration_ms=int(elapsed * 1000),
    )

    st.caption(f"⏱️ Answered in {elapsed:.1f}s")

    if related:
        render_related_questions(related, set_pending_query)
