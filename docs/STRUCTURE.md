# Project Structure

## Directory Overview

```
Financial-News-Agent/
├── src/finnews/              # Main Python package
│   ├── api/                  # FastAPI REST endpoints
│   │   └── main.py          # API server & endpoints
│   ├── ui/                   # Streamlit web interface
│   │   ├── app.py           # Main UI application
│   │   ├── session_manager.py # Session persistence
│   │   └── conversation_history.py # Conversation storage
│   ├── rag/                  # RAG pipeline components
│   │   ├── chunker.py       # Text preprocessing & chunking
│   │   ├── embedder.py      # Vector embedding generation
│   │   ├── retriever.py     # Document retrieval & ranking
│   │   └── rag_chain.py     # LLM response generation
│   ├── scraper/              # Scrapy news scraper
│   │   ├── items.py         # Article data schema
│   │   ├── pipelines.py     # Data processing pipeline
│   │   ├── settings.py      # Scrapy configuration
│   │   ├── runner.py        # Scraper runner utility
│   │   ├── utils.py         # Scraper utilities
│   │   └── spiders/
│   │       └── finviz_spider.py # FinViz news spider
│   ├── scripts/              # CLI utilities
│   │   ├── scrape.py        # Scraping script (scraping only)
│   │   ├── pipeline.py      # Full pipeline orchestrator
│   │   ├── chunk.py         # Chunking script
│   │   ├── embed.py         # Embedding script
│   │   └── cleanup_old_articles.py # Article retention script
│   └── common/               # Shared configuration & utilities
│       ├── config.py        # Centralized settings
│       ├── paths.py         # Path management
│       ├── logging.py       # Logging configuration
│       └── io_utils.py      # File I/O utilities
├── data/                     # Data storage
│   ├── raw_news/            # Scraped articles (JSONL)
│   ├── processed_chunks/    # Text chunks for embedding
│   ├── chroma_store/        # Vector database (articles)
│   ├── chat_memory/         # Vector database (conversations)
│   ├── chat_sessions/       # Session management
│   │   └── conversations/   # Conversation history storage
│   ├── tickers.txt          # Ticker symbols (one per line)
│   └── backups/             # Data backups (created by cleanup)
├── tests/                    # Test suite
│   ├── test_common/         # Common module tests
│   ├── test_rag/            # RAG component tests
│   ├── test_scraper/        # Scraper tests
│   ├── test_api/            # API tests
│   └── test_ui/             # UI tests
├── docs/                     # Documentation
│   ├── Images/              # Screenshots and images
│   ├── RUNBOOK.md          # Operational guide
│   └── STRUCTURE.md        # This file
├── scrapy.cfg               # Scrapy configuration
├── pyproject.toml           # Package configuration
├── env.example              # Environment template
└── README.md               # Main documentation
```

## Component Responsibilities

### API Layer (`src/finnews/api/`)
- **Purpose**: RESTful API for external integrations
- **Key Files**: `main.py` (FastAPI app with lifespan management)
- **Features**: Health checks, vectorstore initialization, chat endpoint
- **Dependencies**: FastAPI, uvicorn

### UI Layer (`src/finnews/ui/`)
- **Purpose**: User-friendly web interface
- **Key Files**:
  - `app.py` - Streamlit app with chat history sidebar
  - `session_manager.py` - Active session management
  - `conversation_history.py` - Conversation persistence
- **Features**: Multi-conversation support, auto-generated titles, source citations
- **Dependencies**: Streamlit, requests

### RAG Pipeline (`src/finnews/rag/`)
- **Purpose**: Core retrieval-augmented generation logic
- **Key Files**:
  - `chunker.py` - Text preprocessing, normalization, and chunking
  - `embedder.py` - Vector embedding generation with factory pattern
  - `retriever.py` - Document retrieval, reranking, and chat memory
  - `rag_chain.py` - LLM response generation with source tracking
- **Features**: Recency-based reranking, ticker filtering, chat memory retrieval
- **Dependencies**: LangChain, ChromaDB, HuggingFace Transformers

### Scraper (`src/finnews/scraper/`)

**Architecture:**
- Direct Scrapy execution (no subprocess isolation)
- Runs in same process as caller (CLI or scheduler)
- Blocking execution model (completes before returning)

**Key Files:**
- `scheduler.py` - Automated scraping scheduler (daily + on-demand)
- `runner.py` - Scraper execution wrapper (direct Scrapy execution)
- `metadata.py` - Scrape metadata and status management
- `pipelines.py` - Item processing pipeline with duplicate detection
- `spiders/finviz_spider.py` - FinViz news spider

**Features:**
- ✅ Automated daily scraping (2 AM UTC default)
- ✅ Loads tickers from data/tickers.txt
- ✅ Incremental scraping with duplicate detection
- ✅ Status tracking via JSON metadata file

**Note:** Scheduled scraping blocks the API server during execution (~30-300 seconds). This is acceptable since scraping runs at 2 AM (low traffic).

**Dependencies:** Scrapy, APScheduler

### Common (`src/finnews/common/`)
- **Purpose**: Shared utilities and configuration
- **Key Files**:
  - `config.py` - Centralized settings with validation
  - `paths.py` - Path initialization utilities
  - `logging.py` - Logging setup and logger factory
  - `io_utils.py` - File I/O utilities (JSONL, JSON, directory creation)
- **Features**: Pydantic settings, environment variable loading, error handling
- **Dependencies**: Pydantic

### Scripts (`src/finnews/scripts/`)
- **Purpose**: CLI utilities for data pipeline
- **Key Files**:
  - `scrape.py` - Manual scraper (scraping only, no auto-processing)
  - `pipeline.py` - Full pipeline orchestrator (cleanup → scrape → chunk → embed)
  - `chunk.py` - Process raw articles into chunks
  - `embed.py` - Generate embeddings and build vector store
  - `cleanup_old_articles.py` - Retention management with selective deletion
- **Features**: Ticker override, configurable cleanup, error handling
- **Note**: `finnews-pipeline` is recommended for production data refreshes

## Data Flow

### Ticker Management Flow
1. User edits `data/tickers.txt` (one ticker per line)
2. Scheduler reads tickers via `ticker_manager.load_tickers()`
3. Scraper processes all tickers from file
4. Articles saved to `data/raw_news/articles.jsonl`

### Full Pipeline Flow (finnews-pipeline)
1. **Cleanup** (optional) → `cleanup_old_articles.py` → selective deletion
2. **Scraping** → `scraper/` → `data/raw_news/articles.jsonl`
3. **Chunking** → `rag/chunker.py` → `data/processed_chunks/chunked_articles.jsonl`
4. **Embedding** → `rag/embedder.py` → `data/chroma_store/`

### Manual Flow (individual commands)
1. **Scraping Only** → `finnews-scrape` → `data/raw_news/articles.jsonl`
2. **Processing** → `finnews-chunk` → `finnews-embed`
3. **Querying** → `ui/` or `api/` → `rag/rag_chain.py` → `data/chroma_store/`
4. **Memory** → `rag/retriever.py` → `data/chat_memory/`
5. **Cleanup** → `finnews-cleanup` → selective deletion from all data stores

## Configuration

### Central Configuration (`src/finnews/common/config.py`)
- OpenAI API key
- LLM model selection (default: gpt-4o-mini)
- Embedding model (default: BAAI/bge-base-en-v1.5)
- API host and port
- Streamlit port
- Data paths
- Scraping scheduler settings

### Environment Variables (`.env`)
- `OPENAI_API_KEY` - Required for LLM
- `LLM_MODEL` - Optional model override
- `EMBEDDING_MODEL` - Optional embedding model override
- `SCRAPE_SCHEDULE_ENABLED` - Enable/disable automated scraping (default: False)
- `SCRAPE_SCHEDULE_HOUR` - Hour for daily scraping (default: 2, UTC)

### Scrapy Configuration (`scrapy.cfg`)
Project-level Scrapy settings

### Package Configuration (`pyproject.toml`)
- Dependencies organized by feature (scraper, api, ui, rag, dev)
- Console scripts for CLI tools
- Testing and linting configuration

## Key Design Patterns

### Factory Pattern
- `get_embedding_model()` - Centralized embedding model creation
- `get_logger()` - Logger instances with consistent configuration

### Utility Functions
- `read_jsonl()` / `write_jsonl()` - Centralized JSONL I/O with error handling
- `read_json()` / `write_json()` - Centralized JSON I/O with error handling
- `ensure_file_dir()` - Directory creation helper
- `load_existing_urls()` - URL deduplication for scraper

### Error Handling
- Graceful degradation with logging
- Corrupted file recovery
- Missing data handling

## Testing

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline testing
- **Coverage**: All major components covered
- **Run Tests**: `python -m pytest tests/ -v`
