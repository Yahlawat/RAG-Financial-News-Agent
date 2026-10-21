# Runbook

How to configure, run and maintain Financial News Agent. For a first-time setup, start with the [Quick start](../README.md#quick-start) in the README.

## Configuration

Settings are read from `.env` in the project root, or from environment variables with the same names. Environment variables take precedence. Copy `.env.example` to get started.

Unknown keys in `.env` cause a startup error (`Extra inputs are not permitted`). Use only the settings below.

### Core

| Setting | Default | Description |
|---------|---------|-------------|
| `OPENAI_API_KEY` | (none) | Required for answering questions. |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI chat model used for answers. |
| `EMBEDDING_MODEL` | `BAAI/bge-base-en-v1.5` | Hugging Face embedding model. If you change it, rebuild the index (see [Rebuild the vector database](#rebuild-the-vector-database)). |
| `API_HOST` | `127.0.0.1` | Address the API binds to. The web interface also uses it to reach the API. |
| `API_PORT` | `8000` | API port. |
| `STREAMLIT_PORT` | `8501` | Web interface port. |
| `DEFAULT_USER_ID` | `default` | User ID that the web interface sends to the API. |

### Scheduling

| Setting | Default | Description |
|---------|---------|-------------|
| `SCRAPE_SCHEDULE_ENABLED` | `false` | Run the daily pipeline from the API server. |
| `SCRAPE_SCHEDULE_HOUR` | `2` | Hour of the daily run, in UTC (0–23). |
| `SCRAPE_SCHEDULE_MINUTE` | `0` | Minute of the daily run (0–59). |
| `SCRAPE_TIMEOUT` | `1800` | Seconds after which a "running" status counts as a crashed run and is reset. |

### Logging

| Setting | Default | Description |
|---------|---------|-------------|
| `LOG_DIR` | `logs/` | Directory for log files. |
| `LOG_LEVEL` | `INFO` | Log level of the API server (uvicorn). |
| `LOG_ROTATION_DAYS` | `30` | Number of daily rotated log files to keep. |
| `LOG_ENABLE_UNIFIED` | `true` | Also write all logs to `logs/combined.log`. |

### File locations

These settings override the default paths. All defaults are relative to the project root.

| Setting | Default |
|---------|---------|
| `TICKERS_FILE` | `data/tickers.txt` |
| `RAW_NEWS_PATH` | `data/raw_news/articles.jsonl` |
| `PROCESSED_CHUNKS_PATH` | `data/processed_chunks/chunked_articles.jsonl` |
| `CHROMA_DIR` | `data/chroma_store/` |
| `CHAT_MEMORY_DIR` | `data/chat_memory/` |
| `CHAT_SESSIONS_FILE` | `data/chat_sessions/chat_sessions.json` |
| `SCRAPE_METADATA_FILE` | `data/scrape_metadata.json` |

## Running the services

```bash
finnews-api   # API server, http://localhost:8000 (interactive docs at /docs)
finnews-ui    # Web interface, http://localhost:8501
```

The web interface sends questions to the API, so start the API first. On startup, the API loads the embedding model and both vector stores. If scheduling is enabled, it also starts the scheduler.

## Data pipeline

`finnews-pipeline` runs these steps in order and stops at the first failure:

| Step | Command | What it does |
|------|---------|--------------|
| 1. Cleanup | `finnews-cleanup` | Backs up the raw articles and chunks files, then removes articles older than 30 days. |
| 2. Scrape | `finnews-scrape` | Fetches news for each ticker and appends articles it hasn't seen before to `data/raw_news/articles.jsonl`. |
| 3. Chunk | `finnews-chunk` | Rebuilds `data/processed_chunks/chunked_articles.jsonl` from all raw articles. |
| 4. Embed | `finnews-embed` | Embeds new chunks and deletes chunks that are no longer in the chunks file from ChromaDB. |

Each step can also be run on its own. `finnews-scrape` and `finnews-pipeline` accept `--tickers AAPL,MSFT` to override `data/tickers.txt`.

Running a step again is safe:
- Scraping skips URLs it has already saved.
- Chunk IDs are derived from each chunk's content, so re-embedding never creates duplicates.

### Changes made while the API is running

The API keeps its vector store open, so changes made by other processes don't reach it. If the API is running when you run `finnews-embed` or `finnews-pipeline` from the command line, restart the API afterwards. The scheduled pipeline runs inside the API and doesn't need a restart.

## Scheduled pipeline

When `SCRAPE_SCHEDULE_ENABLED=true`, the API server runs the full pipeline every day at the configured UTC time:
- **Scraping** runs in a separate process, because Scrapy can't be restarted inside a long-running process.
- **Chunking and embedding** run inside the API process, so new articles are searchable as soon as the run finishes.
- **Overlapping runs are skipped.** If a run is still in progress when the next one starts, the new one is skipped.
- **Crashed runs are reset.** A run that has been "running" for longer than `SCRAPE_TIMEOUT` is treated as crashed, and the status is reset.

Check progress with:

```bash
curl http://localhost:8000/scrape/status
```

The response includes `status` (`idle`, `running`, `completed` or `error`), `pipeline_stage` (`idle`, `scraping`, `chunking`, `embedding`, `completed` or `error`), `articles_found` and `time_elapsed_seconds`.

## Data retention and backups

`finnews-cleanup` keeps articles from the last 30 days. Use `--days N` to change the cutoff and `--no-backup` to skip the backup. It decides each article's age as follows:
- **Articles with a publication date** are judged by that date.
- **Articles without one**, such as links to other sites, are judged by when they were scraped.
- **Chunks** are kept exactly when their article is kept.

If no article falls within the cutoff, cleanup stops without changing any files.

Before each cleanup, the raw articles and chunks files are copied to `data/backups/<YYYYMMDD_HHMMSS>/`. Backups older than 180 days are deleted. The vector database isn't backed up, because it can be rebuilt from the chunks file.

Cleanup doesn't modify the vector database. The next `finnews-embed` removes the deleted chunks from it.

## Data files

| Path | Contents |
|------|----------|
| `data/tickers.txt` | Tickers to scrape, one per line. Lines starting with `#` are ignored. |
| `data/raw_news/articles.jsonl` | Scraped articles, one JSON object per line. |
| `data/processed_chunks/chunked_articles.jsonl` | Article chunks with metadata. |
| `data/chroma_store/` | Vector database of article chunks. |
| `data/chat_memory/` | Vector database of chat messages, used for follow-up questions. |
| `data/chat_sessions/` | Conversation list and history shown in the web interface. |
| `data/scrape_metadata.json` | Status of the current or last pipeline run. |
| `data/backups/` | Backups created by cleanup. |

## Logs

Each component writes to `logs/<component>/<component>.log`:
- `api`, `scraper`, `pipeline` and `rag`
- `scripts`, for cleanup
- `ui`

With `LOG_ENABLE_UNIFIED=true`, all logs are also written to `logs/combined.log`. Log files rotate at midnight.

## Maintenance

### Rebuild the vector database

Rebuild the database after changing `EMBEDDING_MODEL`, or if the index looks inconsistent:

```bash
rm -rf data/chroma_store
finnews-embed
```

Restart the API afterwards if it's running.

### Reset all data

This deletes all articles, indexes and chat history. `data/tickers.txt` is kept.

```bash
rm -rf data/raw_news data/processed_chunks data/chroma_store data/chat_memory \
       data/chat_sessions data/scrape_metadata.json
```

### After updating the code

Reinstall the package so the `finnews-*` commands point at the current code:

```bash
pip install -e ".[scraper,api,ui,rag]"
```

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| Every command fails with `Extra inputs are not permitted` | `.env` contains a setting that doesn't exist. Remove it, or compare your file with `.env.example`. |
| `OPENAI_API_KEY is required` | Set `OPENAI_API_KEY` in `.env`. |
| The web interface can't connect to the API | Start `finnews-api`, and check that `API_HOST` and `API_PORT` match in both processes. |
| Answers don't include recent articles | Run `finnews-pipeline`. If the API was already running, restart it. |
| A scrape reports 0 new articles | Normal when every listed article has already been saved. If you expected new ones, check `logs/scraper/scraper.log` for HTTP errors such as 403. |
| The status stays `running` after a crash | It resets automatically after `SCRAPE_TIMEOUT` seconds. |
| `finnews-*` commands behave like an older version | Reinstall the package (see [After updating the code](#after-updating-the-code)). |
| Port already in use | Find the process with `lsof -i :8000` or `lsof -i :8501`, or change `API_PORT` or `STREAMLIT_PORT`. |

## Deployment

Run the API as a single process:

```bash
finnews-api
# or
uvicorn finnews.api.main:app --host 127.0.0.1 --port 8000
```

Don't use multiple uvicorn workers. Each worker would start its own scheduler, so the daily pipeline would run once per worker, and each worker would load its own copy of the embedding model.

The API has no authentication. Binding it to `0.0.0.0` makes it reachable from your network. Put it behind an authenticating reverse proxy if it needs to be accessible remotely.
