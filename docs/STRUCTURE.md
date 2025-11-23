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
│   │   ├── scrape.py        # Scraping script
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
│   ├── backups/             # Data backups (created by cleanup)
│   └── tickers/             # S&P 500 ticker symbols
│       ├── get_sp500_tickers.py # Ticker fetching utility
│       └── tickers.csv      # Stored ticker list
├── tests/                    # Test suite
│   ├── test_common/         # Common module tests
│   ├── test_rag/            # RAG component tests
│   ├── test_scraper/        # Scraper tests
│   ├── test_api/            # API tests
│   ├── test_ui/             # UI tests
│   └── test_integration/    # Integration tests
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
- **Purpose**: Financial news collection from FinViz
- **Key Files**:
  - `finviz_spider.py` - Main spider with URL deduplication
  - `pipelines.py` - JSONL output pipeline
  - `utils.py` - Common scraper utilities (URL loading)
- **Features**: Incremental scraping, ticker extraction, date parsing
- **Dependencies**: Scrapy

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
  - `scrape.py` - Run news scraper
  - `chunk.py` - Process raw articles into chunks
  - `embed.py` - Generate embeddings and build vector store
  - `cleanup_old_articles.py` - Retention management with selective deletion
- **Features**: Backup creation, selective deletion, no re-processing

## Data Flow

1. **Scraping**: `scraper/` → `data/raw_news/articles.jsonl`
2. **Processing**: `rag/chunker.py` → `data/processed_chunks/chunked_articles.jsonl`
3. **Embedding**: `rag/embedder.py` → `data/chroma_store/`
4. **Querying**: `ui/` or `api/` → `rag/rag_chain.py` → `data/chroma_store/`
5. **Memory**: `rag/retriever.py` → `data/chat_memory/`
6. **Cleanup**: `scripts/cleanup_old_articles.py` → selective deletion from all data stores

## Configuration

### Central Configuration (`src/finnews/common/config.py`)
- OpenAI API key
- LLM model selection (default: gpt-4o-mini)
- Embedding model (default: BAAI/bge-base-en-v1.5)
- API host and port
- Streamlit port
- Data paths

### Environment Variables (`.env`)
See `env.example` for template:
- `OPENAI_API_KEY` - Required for LLM
- `LLM_MODEL` - Optional model override
- `EMBEDDING_MODEL` - Optional embedding model override

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
