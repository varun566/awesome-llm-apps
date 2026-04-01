import json
import os
import streamlit as st
from utils.logger import get_logger

logger = get_logger(__name__)


def load_css() -> None:
    """Inject custom CSS from ui/styles.css into the Streamlit app."""
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_message(role: str, content: str) -> None:
    """Render a chat message with custom styling."""
    if role == "user":
        st.markdown(
            f'<div class="user-message">🧑 {content}</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.chat_message("assistant", avatar="🔍"):
            st.markdown(content)


def render_confidence_badge(score: float) -> str:
    """Return an HTML confidence badge based on a 0–1 score."""
    if score >= 0.7:
        return f'<span class="confidence-high">✅ High Confidence ({score:.0%})</span>'
    if score >= 0.4:
        return f'<span class="confidence-medium">⚠️ Medium Confidence ({score:.0%})</span>'
    return f'<span class="confidence-low">❌ Low Confidence ({score:.0%})</span>'


def render_sources(sources: list) -> None:
    """Render source citations in an expander."""
    if not sources:
        return
    with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
        for i, src in enumerate(sources, 1):
            title = src.get("title", "Untitled")
            url = src.get("href", src.get("url", "#"))
            snippet = src.get("body", src.get("snippet", ""))[:200]
            st.markdown(
                f'<div class="source-card">'
                f"**{i}. [{title}]({url})**<br>"
                f"<small>{snippet}…</small>"
                f"</div>",
                unsafe_allow_html=True,
            )


def render_related_questions(questions: list, callback) -> None:
    """Render related questions as clickable buttons."""
    if not questions:
        return
    st.markdown("**💡 Related Questions**")
    for q in questions:
        if st.button(f"❓ {q}", key=f"rq_{hash(q)}", use_container_width=True):
            callback(q)


def render_cache_stats(cache_stats: dict) -> None:
    """Display cache statistics in the sidebar."""
    st.sidebar.markdown("### 📊 Cache Stats")
    cols = st.sidebar.columns(2)
    cols[0].metric("Size", cache_stats.get("size", 0))
    cols[1].metric("Hit Rate", f"{cache_stats.get('hit_rate', 0):.0%}")
    cols[0].metric("Hits", cache_stats.get("hits", 0))
    cols[1].metric("Misses", cache_stats.get("misses", 0))


def render_analytics_chart(analytics: list) -> None:
    """Render a simple analytics bar chart in the sidebar."""
    if not analytics:
        st.sidebar.info("No analytics data yet.")
        return
    import pandas as pd

    df = pd.DataFrame(analytics)
    if "created_at" in df.columns and "duration_ms" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.sort_values("created_at").tail(20)
        st.sidebar.bar_chart(df.set_index("created_at")["duration_ms"])


def export_conversation(messages: list, fmt: str = "json") -> str:
    """Export conversation history to a JSON or plain-text string."""
    if fmt == "json":
        return json.dumps(messages, indent=2, default=str)
    lines = []
    for m in messages:
        role = m.get("role", "unknown").upper()
        content = m.get("content", "")
        lines.append(f"[{role}]\n{content}\n")
    return "\n".join(lines)
