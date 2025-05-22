# Financial News QA System

A comprehensive system for scraping financial news, processing it, and answering questions using RAG (Retrieval Augmented Generation).

## Project Structure

```
finllm_qa/
├── data/                      # Data storage
├── finnews_scraper/          # Scrapy project for news scraping
├── retriever/                # Text processing and vector storage
├── llm/                      # Model fine-tuning and training
├── rag_pipeline/            # RAG implementation
├── interface/               # Web interfaces
├── deployment/              # Deployment configurations
└── notebooks/              # Development notebooks
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
- Copy `.env.example` to `.env`
- Add your API keys and configuration

## Components

- **News Scraper**: Scrapes financial news from various sources
- **Retriever**: Processes and chunks text, creates embeddings
- **LLM**: Fine-tunes language models on financial data
- **RAG Pipeline**: Combines retrieval and generation
- **Interface**: Web-based UI for interacting with the system

## Usage

1. Start the web interface:
```bash
streamlit run interface/app_streamlit.py
```

2. Or use the API:
```bash
uvicorn deployment.fastapi_server:app --reload
```

## License

MIT 