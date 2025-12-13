# RAG - Financial News Q&A Agent

A production-ready Python-based Retrieval-Augmented Generation (RAG) system designed to answer stock-related questions by scraping, processing, and embedding financial news articles. The system combines web scraping (Scrapy), semantic search (ChromaDB), embeddings (HuggingFace), and LLM-powered responses (OpenAI ChatGPT) to provide contextual, up-to-date financial insights.

<img src="./docs/Images/project_image.png" width="300" alt="project_logo">

## Features

- **Intelligent Web Scraping**: Automated financial news collection from FinViz with 40,000+ articles stored
- **Simple Ticker Management**: File-based ticker configuration (data/tickers.txt)
- **Advanced Text Processing**: Smart chunking and cleaning of articles for optimal embeddings
- **Semantic Search**: Fast, relevant document retrieval using ChromaDB vector database
- **Context-Aware Responses**: RAG-powered Q&A with conversation memory and ticker filtering
- **Clean Interface**: Streamlined Streamlit chat interface and FastAPI REST endpoints
- **Session Management**: Persistent conversation history across sessions
- **Modular Architecture**: Clean separation of concerns with configurable components
- **Easy Installation**: Simple pip install with optional dependency groups

## Sample Conversation

Below is an example conversation demonstrating the system's capabilities:

<img src="./docs/Images/usage_screenshot_1.png" width="750" alt="screenshot_1">
<img src="./docs/Images/usage_screenshot_2.png" width="750" alt="screenshot_2">

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Yahlawat/Financial-News-Agent.git
cd Financial-News-Agent

# Install the package in editable mode with all dependencies
pip install -e .[scraper,api,ui,rag]

# Or install specific components only
pip install -e .[rag]  # Just RAG components
pip install -e .[api,ui]  # Just the interfaces
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Ticker Management

Create and populate your tickers file:

```bash
# Create the tickers file
echo -e "AAPL\nMSFT\nGOOGL\nTSLA" > data/tickers.txt
```

The system will automatically scrape news for all tickers in the file daily (2 AM UTC by default).

**Manual Operations**:
```bash
# Scrape only
finnews-scrape

# Or scrape specific tickers
finnews-scrape --tickers AAPL,MSFT,GOOGL

# Run full pipeline (cleanup → scrape → chunk → embed)
finnews-pipeline

# Or manual step-by-step processing
finnews-chunk
finnews-embed
```

### 4. Run the Application

#### API Server (FastAPI)
```bash
finnews-api
```

#### Web Interface (Streamlit)
```bash
finnews-ui
```

### Console Scripts

```bash
finnews-pipeline            # Full pipeline: cleanup → scrape → chunk → embed (recommended)
finnews-scrape              # Scrape news articles
finnews-chunk               # Process articles into chunks
finnews-embed               # Generate embeddings
finnews-cleanup             # Clean up old articles
finnews-api                 # Start FastAPI server
finnews-ui                  # Start Streamlit web interface
```

📋 **For detailed command options and usage**, see [docs/RUNBOOK.md](docs/RUNBOOK.md)

## Project Architecture

```
Financial-News-Agent/
├── src/finnews/           # Main package
│   ├── api/               # FastAPI REST endpoints
│   ├── ui/                # Streamlit web interface
│   ├── rag/               # RAG pipeline components
│   ├── scraper/           # Scrapy news scraper
│   ├── scripts/           # CLI utilities
│   └── common/            # Shared configuration & utilities
├── data/                  # Data storage
│   ├── tickers.txt        # Ticker symbols (one per line)
│   ├── raw_news/          # Scraped articles
│   ├── processed_chunks/  # Text chunks
│   ├── chroma_store/      # Vector database
│   └── chat_memory/       # Conversation history
├── tests/                 # Test suite
└── docs/                  # Documentation
```

📋 **Detailed structure**: See [docs/STRUCTURE.md](docs/STRUCTURE.md)

## Key Components

### Data Pipeline
- **Automated Scraper**: Scheduled news collection from FinViz with duplicate detection
  - Daily scraping at 2 AM UTC (configurable)
  - Scrapes all tickers from data/tickers.txt
  - Manual scraping available via CLI
- **Chunker**: Intelligent text segmentation optimized for semantic search
- **Embedder**: HuggingFace-based vector embeddings using BAAI/bge-base-en-v1.5

### RAG System
- **Retriever**: Multi-stage document retrieval with ticker filtering and recency scoring
- **Memory**: Persistent conversation context using ChromaDB
- **Generator**: OpenAI GPT-4o-mini for structured, context-aware responses

### Interface
- **Streamlit**: User-friendly web interface with session management
- **FastAPI**: RESTful API for integration with external applications

### Ticker Management

Manage tickers via `data/tickers.txt` (one per line):

```
# My portfolio
AAPL
MSFT
GOOGL
TSLA
```

The system automatically reads this file for scraping operations.

📋 **For scheduler configuration and advanced options**, see [docs/RUNBOOK.md](docs/RUNBOOK.md)

## Configuration

Key settings in `.env`:

| Setting | Environment Variable | Required |
|---------|---------------------|----------|
| **OpenAI API Key** | `OPENAI_API_KEY` | Yes |
| **LLM Model** | `LLM_MODEL` | No (default: `gpt-4o-mini`) |
| **API Port** | `API_PORT` | No (default: 8000) |
| **UI Port** | `STREAMLIT_PORT` | No (default: 8501) |

📋 **For full configuration options**, see [docs/RUNBOOK.md](docs/RUNBOOK.md)

## Advanced Features

### Session Persistence
- Conversations automatically resume across sessions
- User-specific chat history with ChromaDB storage
- Session reset functionality for fresh conversations

### Smart Retrieval
- Document reranking based on publication date recency
- Ticker-specific filtering for focused results
- Conversation context integration for follow-up questions

### Scalable Architecture
- Batch processing for large-scale embedding generation
- Duplicate detection and incremental updates
- Production-ready FastAPI deployment

## License

MIT License - see LICENSE file for details.

---

**Built by Yash Ahlawat** | *Showcasing expertise in RAG systems*
