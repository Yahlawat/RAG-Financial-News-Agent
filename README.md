# RAG - Financial News Q&A Agent

A Python-based Retrieval-Augmented Generation (RAG) system designed to answer stock-related questions by scraping, processing, and embedding financial news articles. Showcases expertise in web scraping (Scrapy), data processing (pandas, NumPy), NLP embeddings (HuggingFace, LangChain), and semantic search (ChromaDB). Utilizes LLMs (Ollama) for generating structured, context-rich responses.

<img src="./Images/project_image.png" width="300" alt="UFC Logo">

## Features

- **Web Scraping:** Scrapes and stores financial news articles (over 40,000+ saved) with metadata via a Scrapy Spider (`finnews_scraper/`).
- **Data Processing & Chunking:** Cleans and slices articles into smaller chunks for efficient embeddings (`processed_chunks/`).
- **Embeddings & Semantic Search:** Generates embeddings using HuggingFace models and stores vectors in ChromaDB (`chroma_store/`) for fast, relevant retrieval.
- **RAG-based Q&A Agent:** Answers stock-related questions using an LLM (Ollama + LangChain).

## Sample Conversation 

Below is an example of a sample conversation with the agent I had with the agent on June 04, 2025:

```
Enter comma-separated tickers to filter by (or press Enter for no filter): TSLA
Starting new chat session. (Type 'exit' or 'quit' to end)

You: What’s the current sentiment on TSLA based on the latest news?

Assistant: Here’s the current sentiment on TSLA based on the latest news:

**Summary:**
The sentiment surrounding Tesla (TSLA) is cautiously negative, driven by recent disappointing sales figures, concerns about Elon Musk’s ventures, and a perception that the stock is undervalued.

**Key Insights:**
1. **Weak Sales Performance:** Tesla’s sales growth has declined by 13% YoY in deliveries.
2. **Musk’s Diversified Spending:** Elon Musk’s use of Tesla’s resources for SpaceX and xAI is raising concerns about capital allocation.
3. **Undervaluation Perception:** Analysts view TSLA as attractively priced, suggesting potential upside amid short-term challenges.

**Reasoning:**
The combination of weak sales, strategic shifts, and analyst views of undervaluation paints a picture of cautious skepticism. The market is weighing long-term potential against current execution challenges.

**What to Watch Next:**
- Monitor Tesla’s next earnings report for signs of a sales turnaround.
- Track developments in Musk’s ventures (SpaceX, xAI) to gauge their impact on TSLA’s resources.

**Sources:**
- “Pre-Markets in the Green as Q1 Earnings Season Gathers Pace” — [FinViz](https://finviz.com/news/30742/pre-markets-in-the-green-as-q1-earnings-season-gathers-pace) (2025-04-22)
- “Why Is Caterpillar (CAT) Up 12.1% Since Last Earnings Report?” — [FinViz](https://finviz.com/news/70521/why-is-caterpillar-cat-up-121-since-last-earnings-report) (2025-05-30)
- “Cathie Wood Goes Bargain Hunting: 1 Monster Artificial Intelligence (AI) Semiconductor Stock She Just Bought on the Dip. (Hint: It's Not Nvidia or AMD.)” — [FinViz](https://finviz.com/news/69069/cathie-wood-goes-bargain-hunting-1-monster-artificial-intelligence-ai-semiconductor-stock-she-just-bought-on-the-dip-hint-its-not-nvidia-or-amd) (2025-05-29)
- “Carlisle (CSL) Up 2.1% Since Last Earnings Report: Can It Continue?” — [FinViz](https://finviz.com/news/65323/carlisle-csl-up-21-since-last-earnings-report-can-it-continue) (2025-05-23)
- “Why Is CSX (CSX) Up 13.1% Since Last Earnings Report?” — [FinViz](https://finviz.com/news/59621/why-is-csx-csx-up-131-since-last-earnings-report) (2025-05-16)
```

```
You: Can you point out any conflicting viewpoints?

Assistant: **Summary:**
Conflicting viewpoints around TSLA stem from differing assessments of sales performance, Musk’s strategic decisions, and the broader economic climate.

**Key Insights:**
1. **Sales vs. Economy:** The Fed sees a healthy economy with low inflation, but Tesla’s sales decline suggests execution issues.
2. **Musk’s Priorities vs. Investors:** Musk’s investments in SpaceX and xAI are strategic, yet investors worry about resource allocation.
3. **Growth Potential vs. Short-Term Performance:** Some view TSLA as undervalued with AI upside, while others focus on immediate sales challenges.

**Reasoning:**
These conflicting views highlight tension between long-term growth potential and short-term execution. Positive economic indicators clash with Tesla’s declining sales.

**What to Watch Next:**
- How Tesla addresses sales and capital allocation.
- Market reaction to xAI developments to see if the AI thesis holds.

**Sources:**
- “Is the Fed on the Right Track?” — [FinViz](https://finviz.com/news/56306/is-the-fed-on-the-right-track) (2025-05-13)
- “Ball Announces CFO Departure” — [FinViz](https://finviz.com/news/64220/ball-announces-cfo-departure) (2025-05-22)
- “Cboe Expands Data Vantage Sales Team to Strengthen Asia Pacific Presence” — [FinViz](https://finviz.com/news/56772/cboe-expands-data-vantage-sales-team-to-strengthen-asia-pacific-presence) (2025-05-13)
- “Did You Catch the Latest From Shopify and Axon Enterprise?” — [FinViz](https://finviz.com/news/55426/did-you-catch-the-latest-from-shopify-and-axon-enterprise) (2025-05-13)
- “Cboe Global Markets Announces Departure of Global President Dave Howson” — [FinViz](https://finviz.com/news/67773/cboe-global-markets-announces-departure-of-global-president-dave-howson) (2025-05-28)
```

```
You: How might these differing perspectives impact TSLA’s near-term stock performance?

Assistant: **Summary:**
These differing perspectives—sales weakness, earnings revisions, and Musk’s strategic shifts—will likely drive continued volatility and cautious near-term performance for TSLA.

**Key Insights:**
1. **Earnings Revisions Impact:** Consensus earnings estimates are 6.74% lower over 30 days, driving negative sentiment.
2. **Sales Weakness Feeds Skepticism:** Declining delivery numbers reinforce concerns about execution.
3. **Musk’s Ventures as Catalyst:** Continued funding of SpaceX and xAI by Tesla adds uncertainty that could exacerbate downward pressure.

**Reasoning:**
Declining sales, negative estimate revisions, and resource allocation concerns create a feedback loop of volatility. Investors will remain cautious until clear turnaround signs appear.

**What to Watch Next:**
- Tesla’s next earnings call for sales stabilization.
- Direction of consensus earnings estimate revisions (Zacks Rank indicator).
- Developments around xAI as a sign of Musk’s strategic focus.

**Sources:**
- “Copart, Inc. (CPRT) Increases Yet Falls Behind Market: What Investors Need to Know” — [FinViz](https://finviz.com/news/56753/copart-inc-cprt-increases-yet-falls-behind-market-what-investors-need-to-know) (2025-05-13)
- “Deciphering Dover (DOV) International Revenue Trends” — [FinViz](https://finviz.com/news/55961/deciphering-dover-dov-international-revenue-trends) (2025-05-13)
- “Dollar General (DG) Ascends While Market Falls: Some Facts to Note” — [FinViz](https://finviz.com/news/49060/dollar-general-dg-ascends-while-market-falls-some-facts-to-note) (2025-05-06)
- “W&T Offshore (WTI) Reports Q1 Loss, Tops Revenue Estimates” — [FinViz](https://finviz.com/news/49033/wt-offshore-wti-reports-q1-loss-tops-revenue-estimates) (2025-05-06)
- “Diamondback Energy (FANG) Stock Falls Amid Market Uptick: What Investors Need to Know” — [FinViz](https://finviz.com/news/39353/diamondback-energy-fang-stock-falls-amid-market-uptick-what-investors-need-to-know) (2025-04-29)

You: exit  
Ending chat. Goodbye!
```

## Project Structure

```
data/                         # All data inputs and outputs
│
├── chat_memory/              # Conversation history (ChromaDB)
├── chroma_store/             # Persisted vector database (ChromaDB)
├── processed_chunks/         # Cleaned, chunked article sections
├── raw_news/                 # Raw scraped articles (JSONL)
├── tickers/                  # Ticker list for scraping financial news (S&P500)
│ ├── get_sp500_tickers.py # Script to fetch S&P 500 tickers
│ └── tickers.csv # Stored list of tickers
```

```
finnews_scraper/             # Scrapy pipeline to fetch news
├── spiders/                 # Spider logic
│ └── finviz_spider.py       # Spider for Finviz news sources
├── items.py                 # Article schema
├── pipelines.py             # Save pipeline
└── settings.py              # Scrapy settings
```

```
rag_pipeline/                # Core RAG components
├── chunker.py               # Text cleaner & chunker
├── embedder.py              # Embedding logic using HuggingFace
├── retriever.py             # Vector store retrieval (Chroma)
└── rag_chain.py             # Prompt + LLM answer generator
```

```
main.py                      # Interactive terminal chat entry point
```

## Getting Started

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper**

   ```bash
   scrapy crawl finviz_news
   ```

3. **Generate Chunks, embeddings & update vectorstore**

   ```bash
   python chunker.py
   ```

   ```bash
   python embedder.py
   ```

4. **Start Q&A session**

   ```bash
   python main.py
   ```

## In Progress / Roadmap

- **Web Frontend**: React-based interface for user questions  
- **Graph Neo4J:** Build Neo4J graphs to improve retrieval process
- **LLM Fine-Tuning**: Domain-adapted financial LLM  

## License

MIT

---

*Built by Yash Ahlawat*


