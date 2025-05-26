# main.py
import subprocess
from data.tickers.get_sp500_tickers import get_sp500_tickers

def run_ticker_scraper():
    tickers = get_sp500_tickers()
    print(f"✅ Retrieved {len(tickers)} S&P 500 tickers.")

# def run_scrapy_crawler():
#     print("🚀 Running news scraper...")
#     subprocess.run(["scrapy", "crawl", "yahoo_spider"], cwd="scraper/financial_news_scraper")

# def run_vector_build():
#     print("🔧 Building vector database...")
#     build_vectorstore()

# def ask_sample_question():
#     print("❓ Asking a test question...")
#     response = ask_question("What is the outlook for Apple?")
#     print("💬", response)

if __name__ == "__main__":
    run_ticker_scraper()
