# Runbook

## Environment Setup

### Prerequisites
- **Python**: 3.10+ (recommended: 3.11)
- **OS**: Windows, macOS, or Linux
- **Memory**: 8GB+ RAM (for embedding generation)
- **Storage**: 2GB+ free space

### Installation Options

#### Option 1: Editable Install (Recommended)
```bash
# Install with all components
pip install -e .[scraper,api,ui,rag,dev]

# Or install specific components
pip install -e .[rag]  # Just RAG components
pip install -e .[api,ui]  # Just interfaces
```

#### Option 2: Local Development
```bash
# Set Python path for local runs
export PYTHONPATH=src  # Linux/macOS
set PYTHONPATH=src     # Windows

# Install dependencies
pip install -r requirements.txt  # If exists
```

## Configuration

### Environment Variables
Create `.env` file from `env.example`:
```bash
cp env.example .env
```

Required settings:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

Optional settings:
```bash
LLM_MODEL=gpt-4o-mini
API_PORT=8000
STREAMLIT_PORT=8501
```

### Data Configuration
- **Tickers**: Edit `data/tickers/tickers.csv` to change scraping scope
- **Paths**: All data paths managed automatically via `src/finnews/common/config.py`

## Commands

### Data Pipeline

#### 1. Scrape Financial News
```bash
# Using console script (after editable install)
finnews-scrape

# Or direct Scrapy command
scrapy crawl finviz_news

# Or Python script
python src/finnews/scraper/runner.py
```

#### 2. Process Articles
```bash
# Using console script
finnews-chunk

# Or direct Python
python src/finnews/rag/chunker.py
```

#### 3. Generate Embeddings
```bash
# Using console script
finnews-embed

# Or direct Python
python src/finnews/rag/embedder.py
```

### Application Services

#### API Server (FastAPI)
```bash
# Using console script
finnews-api

# Or direct uvicorn
uvicorn finnews.api.main:app --host 0.0.0.0 --port 8000

# Development mode (auto-reload)
uvicorn finnews.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Web Interface (Streamlit)
```bash
# Using console script
finnews-ui

# Or direct Streamlit
streamlit run src/finnews/ui/app.py

# Custom port
streamlit run src/finnews/ui/app.py --server.port 8502
```

## Data Paths

| Purpose | Path | Format |
|---------|------|--------|
| **Raw Articles** | `data/raw_news/articles.jsonl` | JSONL |
| **Processed Chunks** | `data/processed_chunks/chunked_articles.jsonl` | JSONL |
| **Vector DB (Articles)** | `data/chroma_store/` | ChromaDB |
| **Vector DB (Chat)** | `data/chat_memory/` | ChromaDB |
| **Sessions** | `data/chat_sessions/chat_sessions.json` | JSON |
| **Tickers** | `data/tickers/tickers.csv` | CSV |

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Solution: Set PYTHONPATH
export PYTHONPATH=src  # Linux/macOS
set PYTHONPATH=src     # Windows
```

#### 2. API Key Issues
```bash
# Check .env file exists and has correct key
cat .env | grep OPENAI_API_KEY
```

#### 3. Port Conflicts
```bash
# Check if ports are in use
netstat -an | grep :8000  # API port
netstat -an | grep :8501  # UI port
```

#### 4. Memory Issues (Embedding)
```bash
# Reduce batch size in embedder.py
# Or process smaller ticker subsets
```

### Reset Operations

#### Clear All Data
```bash
# Remove all generated data
rm -rf data/raw_news/* data/processed_chunks/* data/chroma_store/* data/chat_memory/*
```

#### Reset Sessions Only
```bash
# Clear chat history
rm -f data/chat_sessions/chat_sessions.json
rm -rf data/chat_memory/*
```

#### Rescrape Subset
```bash
# Edit ticker list
nano data/tickers/tickers.csv

# Then re-run scraping
finnews-scrape
```

## Development

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific test categories
python -m pytest tests/test_rag/ -v
python -m pytest tests/test_api/ -v
python -m pytest tests/test_scraper/ -v
```

### Code Quality
```bash
# Linting (if configured)
flake8 src/
black src/
```

## Production Deployment

### API Server
```bash
# Production uvicorn
uvicorn finnews.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (if available)
```bash
# Build image
docker build -t finnews .

# Run container
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key finnews
```

## Monitoring

### Logs
- **API**: Check uvicorn logs
- **Scraper**: Check Scrapy logs
- **Application**: Check `src/finnews/common/logging.py` configuration

### Health Checks
- **API**: `GET http://localhost:8000/health`
- **UI**: `http://localhost:8501`

## Performance Tips

1. **Scraping**: Start with small ticker subsets for testing
2. **Embedding**: Use GPU if available for faster processing
3. **Memory**: Monitor RAM usage during embedding generation
4. **Storage**: Ensure sufficient disk space for vector databases

