# Project Structure

## Directory Overview

```
Financial-News-Agent/
├── src/finnews/
│   ├── api/                  # FastAPI REST endpoints
│   ├── ui/                   # Streamlit web interface
│   ├── rag/                  # RAG pipeline (chunker, embedder, retriever, rag_chain)
│   ├── scraper/              # Scrapy news scraper + scheduler
│   ├── scripts/              # CLI utilities (pipeline, scrape, chunk, embed, cleanup)
│   └── common/               # Config, logging, I/O utilities
├── data/
│   ├── raw_news/            # Scraped articles (JSONL)
│   ├── processed_chunks/    # Text chunks
│   ├── chroma_store/        # Vector DB (articles)
│   ├── chat_memory/         # Vector DB (conversations)
│   ├── tickers.txt          # Ticker symbols
│   └── backups/             # Backups from cleanup
├── tests/                   # Test suite
├── docs/                    # Documentation
└── pyproject.toml          # Package config & CLI scripts
```

## Components

### API (`src/finnews/api/`)
FastAPI server with health checks and chat endpoint.

### UI (`src/finnews/ui/`)
Streamlit interface with session management and conversation history.

### RAG Pipeline (`src/finnews/rag/`)
- `chunker.py` - Text preprocessing and chunking
- `embedder.py` - Vector embeddings (HuggingFace)
- `retriever.py` - Document retrieval with reranking and chat memory
- `rag_chain.py` - LLM response generation (OpenAI)

### Scraper (`src/finnews/scraper/`)
- Automated daily scraping (2 AM UTC default)
- Loads tickers from `data/tickers.txt`
- Duplicate detection
- Blocking execution (~30-300s)

### Common (`src/finnews/common/`)
Shared configuration, logging, and I/O utilities.

### Scripts (`src/finnews/scripts/`)
CLI commands for data pipeline operations.

## Data Flow

1. **Scraping**: `data/tickers.txt` → scraper → `data/raw_news/articles.jsonl`
2. **Processing**: raw articles → chunker → `data/processed_chunks/chunked_articles.jsonl`
3. **Embedding**: chunks → embedder → `data/chroma_store/`
4. **Querying**: user question → retriever + RAG chain → response with sources

## Configuration

- **Environment**: `.env` file (see `.env.example`)
- **Scrapy**: `scrapy.cfg`
- **Package**: `pyproject.toml` (dependencies, CLI scripts)
- **Central config**: `src/finnews/common/config.py`
