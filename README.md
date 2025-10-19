# RAG - Financial News Q&A Agent

A production-ready Python-based Retrieval-Augmented Generation (RAG) system designed to answer stock-related questions by scraping, processing, and embedding financial news articles. The system combines web scraping (Scrapy), semantic search (ChromaDB), embeddings (HuggingFace), and LLM-powered responses (OpenAI ChatGPT) to provide contextual, up-to-date financial insights.

<img src="./docs/Images/project_image.png" width="300" alt="project_logo">

## Features

- **Intelligent Web Scraping**: Automated financial news collection from FinViz with 40,000+ articles stored
- **Advanced Text Processing**: Smart chunking and cleaning of articles for optimal embeddings
- **Semantic Search**: Fast, relevant document retrieval using ChromaDB vector database
- **Context-Aware Responses**: RAG-powered Q&A with conversation memory and ticker filtering
- **Webapp Interface**: Streamlit web app, and FastAPI REST endpoints
- **Session Management**: Persistent conversation history across sessions

## Sample Conversation

Below is an example conversation demonstrating the system's capabilities:

<img src="./docs/Images/usage_screenshot_1.png" width="750" alt="screenshot_1">
<img src="./docs/Images/usage_screenshot_2.png" width="750" alt="screenshot_2">

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd rag-financial-news

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Data Collection & Processing

```bash
# Scrape financial news (this may take several hours for full S&P500, reduce number of tickers for faster scraping)
scrapy crawl finviz_news

# Process and chunk articles
python src/finnews/rag/chunker.py

# Generate embeddings and build vector database
python src/finnews/rag/embedder.py
```

### 4. Run the Application

#### API Server (FastAPI)
```bash
uvicorn finnews.api.main:app --host 0.0.0.0 --port 8000
```

#### Web Interface (Streamlit)
```bash
streamlit run src/finnews/ui/app.py
```

### Optional: Console Scripts
After installing in editable mode, you can use:

```bash
pip install -e .[scraper,api,ui,rag]

finnews-scrape      # Run Scrapy spider
finnews-chunk       # Build chunks from raw articles
finnews-embed       # Build/update Chroma index
finnews-api         # Start FastAPI server
```

## Project Architecture

```
Financial-News-Agent/
├── src/
│   └── finnews/
│       ├── api/                    # FastAPI app
│       │   └── main.py
│       ├── ui/                     # Streamlit app
│       │   ├── app.py
│       │   └── session_manager.py
│       ├── rag/                    # RAG components
│       │   ├── chunker.py
│       │   ├── embedder.py
│       │   ├── retriever.py
│       │   └── rag_chain.py
│       ├── scraper/                # Scrapy project
│       │   ├── items.py
│       │   ├── pipelines.py
│       │   ├── settings.py
│       │   └── spiders/
│       │       └── finviz_spider.py
│       └── common/                 # Shared configuration
│           └── config.py
├── data/
│   ├── raw_news/
│   ├── processed_chunks/
│   ├── chroma_store/
│   ├── chat_memory/
│   ├── chat_sessions/
│   └── tickers/
├── tests/
├── docs/
│   ├── RUNBOOK.md
│   └── STRUCTURE.md
├── scrapy.cfg
├── pyproject.toml
├── requirements.txt
├── .pre-commit-config.yaml
├── .gitignore
└── README.md
```

See docs/STRUCTURE.md for details.

## Key Components

### Data Pipeline
- **Scraper**: Automated collection of financial news from FinViz with duplicate detection
- **Chunker**: Intelligent text segmentation optimized for semantic search
- **Embedder**: HuggingFace-based vector embeddings using BAAI/bge-base-en-v1.5

### RAG System
- **Retriever**: Multi-stage document retrieval with ticker filtering and recency scoring
- **Memory**: Persistent conversation context using ChromaDB
- **Generator**: OpenAI GPT-3.5-turbo for structured, context-aware responses

### Interface
- **Streamlit**: User-friendly web interface with session management
- **FastAPI**: RESTful API for integration with external applications

## Configuration

### Ticker Management
The system uses S&P 500 companies by default. Update `data/tickers/tickers.csv` to modify the scope:

```bash
python data/tickers/get_sp500_tickers.py  # Refresh S&P 500 list
```

### Embedding Model
Default: `BAAI/bge-base-en-v1.5`. To change the model, update both `embedder.py` and `retriever.py`:

```python
model_name = "your-preferred-model"
```

### LLM Configuration  
Default: OpenAI GPT-3.5-turbo. Modify `src/finnews/rag/rag_chain.py`:

```python
llm = ChatOpenAI(model="gpt-4", temperature=0.0, api_key=api_key)
```

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
