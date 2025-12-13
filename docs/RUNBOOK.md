# Runbook

## Setup

### Prerequisites
- Python 3.10+
- 8GB+ RAM
- 2GB+ storage

### Installation
```bash
pip install -e .[scraper,api,ui,rag,dev]
```

### Configuration
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

Manage tickers in `data/tickers.txt` (one per line).

## Commands

### Data Pipeline
```bash
finnews-pipeline              # Full pipeline: cleanup → scrape → chunk → embed
finnews-scrape                # Scrape news only
finnews-chunk                 # Process articles into chunks
finnews-embed                 # Generate embeddings
finnews-cleanup               # Remove old articles (default: 30 days)
```

### Application
```bash
finnews-api                   # Start API server (http://localhost:8000)
finnews-ui                    # Start web interface (http://localhost:8501)
```

### Automated Scraping
Configure in `.env`:
```bash
SCRAPE_SCHEDULE_ENABLED=true  # Enable daily scraping
SCRAPE_SCHEDULE_HOUR=2        # Hour (UTC, 0-23)
```

## Data Paths

| Purpose | Path |
|---------|------|
| Raw Articles | `data/raw_news/articles.jsonl` |
| Processed Chunks | `data/processed_chunks/chunked_articles.jsonl` |
| Vector DB (Articles) | `data/chroma_store/` |
| Vector DB (Chat) | `data/chat_memory/` |
| Tickers | `data/tickers.txt` |

## Troubleshooting

**Import Errors:**
```bash
export PYTHONPATH=src  # Linux/macOS
set PYTHONPATH=src     # Windows
```

**Port Conflicts:**
```bash
netstat -an | grep :8000  # API
netstat -an | grep :8501  # UI
```

**Reset All Data:**
```bash
rm -rf data/raw_news/* data/processed_chunks/* data/chroma_store/* data/chat_memory/*
```

## Development

### Testing
```bash
pytest tests/ -v
```

### Production
```bash
uvicorn finnews.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```
