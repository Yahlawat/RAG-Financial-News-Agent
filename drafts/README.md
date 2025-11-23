# Drafts & Experimental Code

This directory contains **archived experimental code** and **planned future features** from early development. These files are **not part of the main application** and are kept for reference only.

## 📁 Directory Structure

### Root Level (Archived Experiments)
- `app_streamlit.py` - Early Streamlit UI prototype (superseded by `src/finnews/ui/app.py`)
- `chroma_db.py` - ChromaDB integration experiments (now in `src/finnews/rag/embedder.py`)
- `main.py` - Early main entry point (superseded by organized script structure)

### `simantic_chunker/` (Note: "semantic" misspelled)
Experimental semantic text chunking approaches that were tested but not integrated into the main pipeline.

- `simantic_chunker.py` - Alternative chunking algorithm exploration
- `simantic_chunked_articles.jsonl` - Sample output from experiments

**Status**: Not implemented in production. Current chunker uses `RecursiveCharacterTextSplitter` (see `src/finnews/rag/chunker.py`)

### `src/` (Old Test Files)
Early test files and prototypes before the project structure was reorganized:

- `llm_test.py` - LLM integration tests
- `rag_chain.py` - Early RAG chain implementation
- `retriever.py` - Early retrieval logic
- `tests_rag.py` - RAG pipeline tests
- `test_scraped_news.py` - Scraper output validation
- `webscraping_test.py` - Web scraping experiments

**Status**: Superseded by comprehensive test suite in `tests/` directory

### `to_impliment/Graph/` ⭐ Future Work
**Neo4j graph database integration** for enhanced financial entity relationship tracking.

- `ingest_graph.py` - Graph ingestion pipeline (stub)
- `neo4j_connection.py` - Neo4j connection utilities (stub)
- `query_graph.py` - Graph query interface (stub)
- `__init__.py` - Package initialization

**Status**: 🚧 **Planned but not implemented**

This would enable:
- Entity extraction from news articles (companies, people, events)
- Relationship mapping between S&P 500 companies
- Graph-based retrieval augmenting vector similarity
- Network analysis of financial news connections

**Implementation Notes**:
- Requires Neo4j instance (local or cloud)
- Would integrate with existing RAG pipeline
- Consider LangChain's `Neo4jGraph` integration
- Needs entity recognition (spaCy/Transformers)

## 🗑️ Safe to Delete?

**Recommendation**: Keep this directory for now as reference material, but exclude from production builds.

To exclude from Docker images or distributions, ensure `drafts/` is in `.dockerignore` (when created).

## 🔮 Future Enhancements

If implementing the Graph DB feature:
1. Set up Neo4j instance (Docker recommended)
2. Implement entity extraction in chunking pipeline
3. Create graph schema for financial entities
4. Integrate graph retrieval with vector retrieval
5. Add graph-based analytics endpoints

---

*Last updated: 2025*
