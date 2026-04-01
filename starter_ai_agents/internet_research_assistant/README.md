# 🔍 Internet Research Assistant

A **production-ready**, multi-agent Internet Research Assistant that searches the web in real time, verifies answers across multiple sources, and streams well-cited responses — all from a clean Streamlit UI.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🌐 **Real-time Web Search** | DuckDuckGo search with concurrent multi-query support |
| 🤖 **Multi-Agent Pipeline** | Web Search → Research Analyst → Response Writer |
| ✅ **Answer Verification** | Cross-references multiple sources & scores confidence |
| ⚡ **Streaming Responses** | Token-by-token streaming for instant feedback |
| 💾 **Conversation Persistence** | SQLite stores full chat history across sessions |
| 🚀 **Smart Caching** | TTL-based in-memory + SQLite cache to reduce API calls |
| 📊 **Analytics Dashboard** | Query history, response times, cache hit/miss metrics |
| 📤 **Export** | Download conversations as JSON or plain text |
| 💡 **Related Questions** | Auto-generated follow-up suggestions |

---

## 🏗️ Project Structure

```
internet_research_assistant/
├── app.py                  # Main Streamlit application
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   └── settings.py         # Centralised configuration (env-based)
├── agents/
│   ├── __init__.py
│   ├── web_search_agent.py # DuckDuckGo search with caching
│   ├── research_agent.py   # LLM-powered analysis & verification
│   └── writer_agent.py     # Streaming response synthesis
├── utils/
│   ├── __init__.py
│   ├── cache.py            # Thread-safe TTL in-memory cache
│   ├── database.py         # SQLite persistence layer
│   ├── helpers.py          # Shared utilities
│   └── logger.py           # Rotating-file + console logger
├── models/
│   ├── __init__.py
│   └── schemas.py          # Dataclass schemas
├── ui/
│   ├── __init__.py
│   ├── components.py       # Reusable Streamlit components
│   └── styles.css          # Custom CSS (chat bubbles, badges…)
└── tests/
    ├── __init__.py
    ├── test_cache.py       # TTLCache unit tests
    └── test_agents.py      # Helper & database unit tests
```

---

## 🚀 Quick Start

### 1. Clone & navigate
```bash
git clone https://github.com/varun566/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/internet_research_assistant
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

### 5. Run the app
```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501** 🎉

---

## ⚙️ Configuration

All settings can be provided via environment variables or the `.env` file:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |
| `MAX_SEARCH_RESULTS` | `5` | Results per DuckDuckGo query |
| `MAX_CONCURRENT_SEARCHES` | `3` | Parallel search threads |
| `CACHE_TTL_SECONDS` | `3600` | Cache expiry (seconds) |
| `CACHE_MAX_SIZE` | `100` | Maximum in-memory cache entries |
| `DB_PATH` | `research_assistant.db` | SQLite database file path |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LOG_FILE` | *(empty)* | Optional log file path |

---

## 🤖 Multi-Agent Architecture

```
User Question
     │
     ▼
┌─────────────────────────────────────────────┐
│  Web Search Agent                           │
│  • Runs 1-3 DuckDuckGo queries concurrently │
│  • TTL cache (memory + SQLite)              │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  Research Agent                             │
│  • Cross-references sources                 │
│  • Identifies conflicts / gaps              │
│  • Confidence assessment                    │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  Writer Agent                               │
│  • Streams markdown response                │
│  • Inline source citations                  │
│  • Related questions generation             │
└─────────────────────────────────────────────┘
```

---

## 🧪 Running Tests

```bash
# From the project root
pip install pytest
pytest tests/ -v
```

---

## 📦 Tech Stack

| Component | Technology |
|---|---|
| **UI** | Streamlit |
| **LLM** | OpenAI GPT-4o (configurable) |
| **Web Search** | DuckDuckGo (`duckduckgo-search`) |
| **Caching** | In-memory TTLCache + SQLite |
| **Persistence** | SQLite (via Python `sqlite3`) |
| **Logging** | Python `logging` (rotating file) |
| **Config** | `python-dotenv` |

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

MIT — see the root [LICENSE](../../LICENSE) file.
