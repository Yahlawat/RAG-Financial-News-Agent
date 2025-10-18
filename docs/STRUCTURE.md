# Project Structure

Recommended directories and responsibilities after the re-org.

- src/finnews/
  - api/: FastAPI app (production interface)
  - ui/: Streamlit app (human interface)
  - rag/: Chunking, embedding, retrieval, chat chain
  - scraper/: Scrapy project with spider and pipelines
  - common/: Reserved for shared config/utilities (future)
- data/
  - raw_news/: Source articles from scraper (JSONL)
  - processed_chunks/: Chunked text
  - chroma_store/: Vector DB for articles
  - chat_memory/: Vector DB for conversation memory
  - chat_sessions/: Simple session mapping for UI
  - tickers/: S&P500 list (CSV + script)
- tests/: Unit tests for RAG and (future) API/scraper
- docs/: Docs, ADRs, drafts
- Images/: Existing screenshots used by README

Notes
- UI should only call API for production use. Direct vector-store access is acceptable for local demos.
- Hardcoded paths will be migrated to a central config in a follow-up (finnews/common/config.py).

