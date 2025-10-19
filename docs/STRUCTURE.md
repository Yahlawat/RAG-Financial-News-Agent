# Project Structure

## Directory Overview

```
Financial-News-Agent/
├── src/finnews/              # Main Python package
│   ├── api/                  # FastAPI REST endpoints
│   │   ├── main.py          # API server & endpoints
│   │   └── routers/         # Additional route modules
│   ├── ui/                   # Streamlit web interface
│   │   ├── app.py           # Main UI application
│   │   └── session_manager.py # Session persistence
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
│   │   └── spiders/
│   │       └── finviz_spider.py # FinViz news spider
│   ├── scripts/              # CLI utilities
│   │   ├── scrape.py        # Scraping script
│   │   ├── chunk.py         # Chunking script
│   │   └── embed.py         # Embedding script
│   └── common/               # Shared configuration
│       ├── config.py        # Centralized settings
│       ├── paths.py         # Path management
│       └── logging.py       # Logging configuration
├── data/                     # Data storage
│   ├── raw_news/            # Scraped articles (JSONL)
│   ├── processed_chunks/    # Text chunks for embedding
│   ├── chroma_store/        # Vector database (articles)
│   ├── chat_memory/         # Vector database (conversations)
│   ├── chat_sessions/       # Session management
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
├── config/                   # Configuration files
│   └── scrapy.cfg          # Scrapy configuration
├── pyproject.toml           # Package configuration
├── env.example              # Environment template
└── README.md               # Main documentation
```

## Component Responsibilities

### API Layer (`src/finnews/api/`)
- **Purpose**: RESTful API for external integrations
- **Key Files**: `main.py` (FastAPI app), `routers/` (route modules)
- **Dependencies**: FastAPI, uvicorn

### UI Layer (`src/finnews/ui/`)
- **Purpose**: User-friendly web interface
- **Key Files**: `app.py` (Streamlit app), `session_manager.py` (persistence)
- **Dependencies**: Streamlit, requests

### RAG Pipeline (`src/finnews/rag/`)
- **Purpose**: Core retrieval-augmented generation logic
- **Key Files**: 
  - `chunker.py` - Text preprocessing and chunking
  - `embedder.py` - Vector embedding generation
  - `retriever.py` - Document retrieval and ranking
  - `rag_chain.py` - LLM response generation
- **Dependencies**: LangChain, ChromaDB, HuggingFace

### Scraper (`src/finnews/scraper/`)
- **Purpose**: Financial news collection
- **Key Files**: `finviz_spider.py` (main spider), `pipelines.py` (data processing)
- **Dependencies**: Scrapy

### Common (`src/finnews/common/`)
- **Purpose**: Shared utilities and configuration
- **Key Files**: `config.py` (settings), `paths.py` (path management)
- **Dependencies**: Pydantic

## Data Flow

1. **Scraping**: `scraper/` → `data/raw_news/`
2. **Processing**: `rag/chunker.py` → `data/processed_chunks/`
3. **Embedding**: `rag/embedder.py` → `data/chroma_store/`
4. **Querying**: `ui/` or `api/` → `rag/` → `data/chroma_store/`
5. **Memory**: `rag/` → `data/chat_memory/`

## Configuration

- **Central Config**: `src/finnews/common/config.py`
- **Environment**: `.env` file (see `env.example`)
- **Scrapy Config**: `config/scrapy.cfg`
- **Package Config**: `pyproject.toml`

## Testing

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline testing
- **Coverage**: All major components covered
- **Run Tests**: `python -m pytest tests/ -v`

