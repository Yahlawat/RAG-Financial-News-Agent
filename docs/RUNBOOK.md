# Runbook

Environment
- Python 3.10+
- Set `PYTHONPATH=src` for local runs without install
- Optional: `pip install -r requirements.txt` or `pip install -e .[scraper,api,ui,rag,dev]`

Commands
- Scrape: `scrapy crawl finviz_news`
  - Uses `scrapy.cfg` -> `finnews.scraper.settings`
- Chunk: `python src/finnews/rag/chunker.py` (or `finnews-chunk` after editable install)
- Embed: `python src/finnews/rag/embedder.py` (or `finnews-embed`)
- API: `uvicorn finnews.api.main:app --host 0.0.0.0 --port 8000` (or `finnews-api`)
- UI: `streamlit run src/finnews/ui/app.py`

Data Paths
- Articles: `data/raw_news/articles.jsonl`
- Chunked: `data/processed_chunks/chunked_articles.jsonl`
- Vector DB (articles): `data/chroma_store/`
- Vector DB (chat): `data/chat_memory/`
- Sessions: `data/chat_sessions/chat_sessions.json`

Tips
- To reset session history, delete `data/chat_sessions/chat_sessions.json` and `data/chat_memory/`.
- To rescrape a smaller subset, edit `data/tickers/tickers.csv`.

