# get_sp500_tickers.py
import os
import requests
import pandas as pd

def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    tickers = df['Symbol'].tolist()[:1]  #! Limit for testing
    return tickers

if __name__ == "__main__":
    # Ensure output directory exists
    output_dir = "data/tickers"
    os.makedirs(output_dir, exist_ok=True)

    # Get new tickers
    output_file = os.path.join(output_dir, "tickers.csv")
    tickers = get_sp500_tickers()
    new_df = pd.DataFrame(tickers, columns=['Symbol'])
    new_df['ticker_symbol'] = new_df['Symbol'].str.strip()
    new_df.drop(columns=['Symbol'], inplace=True)

    # Read existing CSV if it exists and append new values
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        # Combine existing and new, drop duplicates
        combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['ticker_symbol'])
        combined_df.to_csv(output_file, index=False)
    else:
        # If no existing file, just write the new data
        new_df.to_csv(output_file, index=False)
