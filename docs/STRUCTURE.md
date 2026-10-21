# Architecture

This document describes how Financial News Agent is organized: its modules, how data moves through the system, the file formats it uses, and the reasoning behind its main design decisions.

## Overview

The system has two halves that share the `data/` directory:

- **Ingestion** (`scraper/`, `rag/chunker.py`, `rag/embedder.py`). Turns ticker symbols into searchable article chunks. It runs from the command line or on a schedule inside the API server.
- **Question answering** (`api/`, `ui/`, `rag/retriever.py`, `rag/rag_chain.py`). Retrieves relevant chunks for a question and asks an OpenAI model to answer from them.

## Directory layout

```
Financial-News-Agent/
├── src/finnews/
│   ├── api/
│   │   ├── main.py                 # FastAPI app: /health, /chat, startup and shutdown
│   │   └── scraper_endpoints.py    # /scrape/status, /scrape/tickers/metadata
│   ├── ui/
│   │   ├── app.py                  # Streamlit chat interface (calls the API)
│   │   ├── conversation_history.py # Stored conversations shown in the sidebar
│   │   └── session_manager.py      # Active conversation per user
│   ├── rag/
│   │   ├── chunker.py              # Raw articles → chunks
│   │   ├── embedder.py             # Chunks → ChromaDB, kept in sync with the chunks file
│   │   ├── retriever.py            # Similarity search, reranking, chat memory
│   │   └── rag_chain.py            # Prompt construction and the OpenAI call
│   ├── scraper/
│   │   ├── spiders/finviz_spider.py  # Finviz news spider
│   │   ├── pipelines.py            # Saves new articles, skipping known URLs
│   │   ├── runner.py               # Runs the spider and records the run status
│   │   ├── scheduler.py            # Daily pipeline inside the API server
│   │   ├── metadata.py             # Run status in data/scrape_metadata.json
│   │   └── settings.py             # Scrapy settings
│   ├── scripts/                    # Entry points for the finnews-* commands
│   │   ├── pipeline.py             # cleanup → scrape → chunk → embed
│   │   ├── scrape.py, chunk.py, embed.py
│   │   └── cleanup_old_articles.py # Retention and backups
│   └── common/
│       ├── config.py               # Settings (environment variables and .env)
│       ├── logging.py              # Log handlers and rotation
│       ├── io_utils.py             # JSON and JSONL helpers
│       ├── paths.py                # Creates data directories
│       └── ticker_manager.py       # Reads and writes data/tickers.txt
├── data/                           # Created at runtime (see docs/RUNBOOK.md)
├── tests/
├── docs/
├── pyproject.toml                  # Dependencies, extras and finnews-* commands
└── scrapy.cfg
```

## Data flow

### Ingestion

1. **Scrape** (`scraper/`). The spider requests each ticker's Finviz page and collects every news link. For links to Finviz-hosted articles, it also fetches the article to get its body, publication date and the tickers it mentions. Links to other sites are saved with only their headline and source. The item pipeline appends articles whose URL isn't already in `articles.jsonl`.
2. **Chunk** (`rag/chunker.py`). It rebuilds the chunks file from all raw articles. Each article body is normalized and split into chunks of about 800 characters with 200 characters of overlap. Articles without a body are skipped.
3. **Embed** (`rag/embedder.py`). It compares the chunks file with the IDs already in ChromaDB, then embeds and adds the missing chunks. Documents that no longer appear in the file are deleted.
4. **Clean up** (`scripts/cleanup_old_articles.py`). It removes articles past the retention cutoff from the raw and chunks files. The next embed removes them from ChromaDB.

### Question answering

1. The web interface sends `POST /chat` with the question and a conversation ID.
2. If the request has no tickers, the API uses the tickers in `data/tickers.txt`.
3. The retriever fetches the 15 chunks most similar to the question and reranks them:
   - Older articles get a lower score.
   - Chunks that mention a requested ticker get a boost.
   - Very short chunks get a penalty.

   The top 5 chunks are kept.
4. The three most relevant earlier messages from the same conversation are retrieved from the chat memory store.
5. `rag_chain.py` builds a prompt from these and calls the OpenAI model. It stores the question and answer in chat memory and returns the answer with the source articles.

## Data formats

**Raw article** (`data/raw_news/articles.jsonl`, one object per line):

```json
{
  "title": "Apple shares rise after earnings",
  "url": "https://finviz.com/news/123456/...",
  "source": "Reuters",
  "scraped_at": "2026-10-21T05:53:49+00:00",
  "published_date": "2026-10-20T16:05:00",
  "body": "Full article text, empty for links to other sites",
  "main_ticker": "AAPL",
  "relevant_tickers": ["AAPL", "MSFT"]
}
```

`published_date` is `null` when it isn't available. That covers all links to other sites.

**Chunk** (`data/processed_chunks/chunked_articles.jsonl`):

```json
{
  "content": "Chunk text...",
  "metadata": {
    "title": "Apple shares rise after earnings",
    "url": "https://finviz.com/news/123456/...",
    "relevant_tickers": ["AAPL", "MSFT"],
    "published_date": "2026-10-20T16:05:00"
  }
}
```

`relevant_tickers` always includes the ticker the article was scraped for. In ChromaDB, the list is stored as a comma-separated string, and missing values are stored as empty strings.

## Design decisions

**The chunks file is the source of truth for the index.** Each chunk's ID is a SHA-1 hash of its text and metadata. As a result:
- Re-running the embedder is idempotent.
- Reordering the chunks file, as cleanup does, doesn't create duplicates.
- A chunk whose text or metadata changed is replaced rather than duplicated.

Because the embedder deletes whatever isn't in the file, cleanup only needs to edit files. As a safeguard, an empty chunks file never wipes the index.

**Scraping runs in a child process when scheduled.** Scrapy runs on Twisted, whose event loop must run in the main thread and can't be restarted. The scheduler therefore starts each scrape in a fresh process. Command-line runs already run Scrapy in their own main thread.

**Chunking and embedding run inside the API process when scheduled.** ChromaDB clients don't see changes made by other processes. When the API's own client writes the new chunks, they become searchable immediately. Command-line runs while the API is up require an API restart.

**Run status lives in a JSON file.** The scraper child process and the API both update `data/scrape_metadata.json`, so writes go to a temporary file that then replaces the original. A reader never sees a partially written file.

**Logging is configured in entry points only.** Library modules only create loggers. Each `finnews-*` command, the API and the web interface set up their own handlers, so importing a module never redirects another component's logs. Scrapy's own root log handler is disabled so that each line is logged once.

## Configuration

- **Runtime settings:** `src/finnews/common/config.py`, set through `.env` or environment variables. See [RUNBOOK.md](RUNBOOK.md#configuration).
- **Scrapy settings:** `src/finnews/scraper/settings.py`. These cover crawl rate, retries and robots.txt.
- **Packaging:** `pyproject.toml` defines the dependencies, the optional extras (`scraper`, `api`, `ui`, `rag`, `dev`) and the `finnews-*` commands.
