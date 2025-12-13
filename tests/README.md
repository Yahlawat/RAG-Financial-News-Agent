# Test Suite Guide

## Test Files

### Critical (Must Pass)
- `test_rag/test_rag_chain.py` - Core Q&A functionality
- `test_scraper/test_scheduler.py` - Automated scraping
- `test_api/test_main.py` - API endpoints

### Important
- `test_scraper/test_runner.py` - Multi-ticker scraping
- `test_rag/test_chunker.py` - Text processing
- `test_scraper/test_spider.py` - Scraping & duplicate detection
- `test_scraper/test_pipeline.py` - Data persistence

### Supporting
- `test_rag/test_embedder.py` - Embeddings
- `test_common/test_config.py` - Configuration

## Running Tests

**All tests:**
```bash
pytest tests/
```

**Critical tests only:**
```bash
pytest tests/test_rag/test_rag_chain.py \
       tests/test_scraper/test_scheduler.py \
       tests/test_api/test_main.py
```

**By component:**
```bash
pytest tests/test_rag/         # RAG system
pytest tests/test_scraper/     # Scraper
pytest tests/test_api/         # API
```

**With coverage:**
```bash
pytest --cov=finnews --cov-report=html tests/
```

**Specific test:**
```bash
pytest tests/test_rag/test_rag_chain.py::TestRagChat -v
```

## Troubleshooting

**Import errors:**
```bash
pip install -e .[dev]
```

**Run with debug output:**
```bash
pytest tests/test_rag/test_rag_chain.py -v -s
```
