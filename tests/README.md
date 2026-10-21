# Tests

The test suite covers the scraper, the ingestion pipeline, retrieval and answer generation, and the API. Network access, OpenAI, ChromaDB and the embedding model are mocked. The suite therefore runs offline in a few seconds and doesn't need an API key.

## Setup

```bash
pip install -e ".[scraper,api,ui,rag,dev]"
```

## Running the tests

```bash
pytest                                    # Full suite
pytest tests/test_rag/                    # One component
pytest tests/test_rag/test_rag_chain.py   # One file
pytest tests/test_rag/test_rag_chain.py::TestRagChat::test_rag_chat_basic_question  # One test
pytest -v -s                              # Verbose, with print and log output
pytest --cov=finnews --cov-report=html    # Coverage report in htmlcov/
```

`pyproject.toml` adds `src/` to the import path and passes `-q` by default.

## Layout

| File | Covers |
|------|--------|
| `test_api/test_main.py` | `/health` and `/chat`: request validation, default tickers, error handling. |
| `test_rag/test_rag_chain.py` | Answer generation: prompt contents, sources, chat memory, a missing API key, LLM failures. |
| `test_rag/test_chunker.py` | Text cleaning, chunk sizes and chunk metadata. |
| `test_rag/test_embedder.py` | Loading chunks, content-based IDs, and keeping the index in sync with the chunks file. |
| `test_scraper/test_spider.py` | Request generation and parsing of Finviz pages. |
| `test_scraper/test_pipeline.py` | Saving articles and skipping duplicate URLs. |
| `test_scraper/test_runner.py` | Running the spider and recording the run status. |
| `test_scraper/test_scheduler.py` | Scheduler start and stop, the daily job, and the scraper subprocess. |
| `test_scripts/test_run_pipeline.py` | Order of the pipeline steps and failure handling. |
| `test_scripts/test_cleanup.py` | Date-based retention and filtering of chunks by kept articles. |
| `test_common/test_config.py` | Settings defaults, environment variables and paths. |

Shared fixtures, such as sample articles and a temporary data directory, are defined in `conftest.py`.

## Writing tests

- **Mock external services.** Patch HTTP requests, OpenAI (`finnews.rag.rag_chain.ChatOpenAI`), ChromaDB and `HuggingFaceEmbeddings` so tests stay fast and offline.
- **Patch names where they're looked up.** For example, patch `finnews.scraper.scheduler.run_pipeline`, not the function in `finnews.scripts.pipeline`.
- **Use temporary files for file I/O.** Use pytest's `tmp_path` or `tempfile` instead of the real `data/` directory.
