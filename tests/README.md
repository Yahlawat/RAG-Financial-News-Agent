# Test Suite Guide

## Quick Reference

### Test Files by Priority

#### **CRITICAL (Must Pass Before Deploy)**
1. `test_rag/test_rag_chain.py` - Core Q&A functionality
2. `test_ui/test_user_profile.py` - Ticker validation & portfolio management
3. `test_scraper/test_scheduler.py` - Automated scraping
4. `test_api/test_main.py` - API endpoints

#### **IMPORTANT (High Risk Areas)**
5. `test_scraper/test_runner.py` - Multi-ticker scraping & timeouts
6. `test_rag/test_chunker.py` - Text processing quality
7. `test_scraper/test_spider.py` - Data scraping & duplicate detection
8. `test_scraper/test_pipeline.py` - Data persistence

#### **SUPPORTING**
9. `test_rag/test_embedder.py` - Vector embedding generation
10. `test_common/test_config.py` - Configuration loading

---

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Critical Tests Only (Fast - ~30s)
```bash
pytest tests/test_rag/test_rag_chain.py \
       tests/test_ui/test_user_profile.py \
       tests/test_scraper/test_scheduler.py \
       tests/test_api/test_main.py
```

### Run by Component

**RAG System**
```bash
pytest tests/test_rag/
```

**Scraping System**
```bash
pytest tests/test_scraper/
```

**API**
```bash
pytest tests/test_api/
```

**User Management**
```bash
pytest tests/test_ui/
```

### Run with Coverage
```bash
# HTML report
pytest --cov=finnews --cov-report=html tests/

# Terminal report
pytest --cov=finnews --cov-report=term-missing tests/
```

### Run Specific Test Class
```bash
# Example: Test only RAG chat functionality
pytest tests/test_rag/test_rag_chain.py::TestRagChat

# Example: Test only ticker validation
pytest tests/test_ui/test_user_profile.py::TestValidateTicker
```

---

## Test Scenarios

### Before Deploying
```bash
# Run all critical tests
pytest tests/test_rag/test_rag_chain.py \
       tests/test_ui/test_user_profile.py \
       tests/test_scraper/test_scheduler.py \
       tests/test_api/test_main.py \
       -v
```

### After RAG Changes
```bash
pytest tests/test_rag/ -v
```

### After Scraper Changes
```bash
pytest tests/test_scraper/ -v
```

### After API Changes
```bash
pytest tests/test_api/ -v
```

### After Ticker/User Profile Changes
```bash
pytest tests/test_ui/test_user_profile.py -v
```

---

## Test Coverage by Feature

### Question Answering (RAG)
- **File**: `test_rag/test_rag_chain.py`
- **Tests**: End-to-end Q&A, source extraction, conversation memory
- **Covers**: Main user-facing feature

### Ticker Management
- **File**: `test_ui/test_user_profile.py`
- **Tests**: Validation, portfolio CRUD, scraping triggers
- **Covers**: Data quality and automation triggers

### Automated Scraping
- **Files**: `test_scraper/test_scheduler.py`, `test_scraper/test_runner.py`
- **Tests**: Scheduled jobs, on-demand scraping, timeout handling
- **Covers**: Background automation

### Data Collection
- **Files**: `test_scraper/test_spider.py`, `test_scraper/test_pipeline.py`
- **Tests**: Web scraping, duplicate detection, data persistence
- **Covers**: Data ingestion pipeline

### Text Processing
- **Files**: `test_rag/test_chunker.py`, `test_rag/test_embedder.py`
- **Tests**: Chunking, cleaning, embedding generation
- **Covers**: RAG data preparation

### API Endpoints
- **File**: `test_api/test_main.py`
- **Tests**: Health check, chat endpoint, error handling
- **Covers**: External interface

---

## What's Tested vs Not Tested

### Tested
- RAG question answering flow
- Ticker validation and portfolio management
- Automated scraping (scheduled + on-demand)
- Multi-ticker scraping with timeouts
- Text chunking and cleaning
- Duplicate detection (URLs, documents)
- API endpoint error handling
- Configuration loading

### Not Tested (Acceptable)
- UI rendering (Streamlit framework handles this)
- Logging functionality (non-critical)
- Trivial helper functions
- Database schema (handled by ChromaDB)

---

## Debugging Failed Tests

### Common Failures

**Import Errors**
```bash
# Install dev dependencies
pip install -e .[dev]
```

**Fixture Not Found**
```bash
# Check conftest.py is in tests/ directory
ls tests/conftest.py
```

**Mock Errors**
```bash
# Check patch paths match actual import structure
# Example: "finnews.api.main.rag_chat" not "rag_chat"
```

**Async Errors**
```bash
# Install pytest-asyncio if needed
pip install pytest-asyncio
```

### Running Individual Tests
```bash
# Run single test function
pytest tests/test_rag/test_rag_chain.py::TestRagChat::test_rag_chat_basic_question -v

# Run with print statements
pytest tests/test_rag/test_rag_chain.py::TestRagChat::test_rag_chat_basic_question -v -s
```

---

## Adding New Tests

### When to Add a Test
1. **New Feature**: Test the core business logic
2. **Bug Fix**: Add test that would have caught the bug
3. **Integration Point**: Test error handling

### Test Structure
```python
class TestYourFeature:
    """Test description of what you're testing."""

    def test_happy_path(self):
        """Test the normal successful case."""
        # Arrange
        # Act
        # Assert

    def test_error_handling(self):
        """Test error scenarios."""
        # Arrange
        # Act
        # Assert
```

### Test Naming Convention
```python
# Format: test_<feature>_<scenario>
test_rag_chat_basic_question()
test_validate_ticker_empty_string()
test_scheduler_start_already_running()
```

---

## CI/CD Integration

### Pre-commit Hook
```bash
# Run critical tests before commit
pytest tests/test_rag/test_rag_chain.py \
       tests/test_ui/test_user_profile.py \
       tests/test_api/test_main.py
```

### GitHub Actions (Example)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -e .[dev]
      - run: pytest tests/ --cov=finnews --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## Performance Considerations

### Test Execution Time

**Fast Tests** (~20s total):
- test_common/test_config.py
- test_ui/test_user_profile.py

**Medium Tests** (~1min total):
- test_rag/test_rag_chain.py
- test_api/test_main.py

**Slow Tests** (~2min total):
- test_scraper/* (filesystem I/O)
- test_rag/test_embedder.py (mock overhead)

### Optimizing Test Speed
1. Use fixtures for shared setup
2. Mock external dependencies (OpenAI API, file I/O)
3. Use temporary directories (tempfile)
4. Run critical tests first for fast feedback

---

## Maintenance

### Monthly Review
1. Check for deprecated tests
2. Update mocks if API changes
3. Remove tests for deleted features

### After Major Refactor
1. Run full test suite
2. Update tests that fail due to interface changes
3. Don't change passing tests unless behavior changed

---

