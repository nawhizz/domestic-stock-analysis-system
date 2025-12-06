import FinanceDataReader as fdr
import pandas as pd
import os
from tqdm import tqdm
from datetime import datetime, timedelta

# Configuration
LIMIT = None  # Limit number of stocks for testing speed (Set to None for full download)
START_DATE = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d') # 2 Years data
DATA_DIR = '.'
PRICES_FILE = os.path.join(DATA_DIR, 'daily_prices.csv')

def get_stock_list():
    """Fetch KOSPI and KOSDAQ stock lists."""
    print("Fetching stock lists...")
    try:
        kospi = fdr.StockListing('KOSPI')
        kosdaq = fdr.StockListing('KOSDAQ')
        
        # Add market tag
        kospi['Market'] = 'KOSPI'
        kosdaq['Market'] = 'KOSDAQ'
        
        # Select important columns (Code, Name, Market, Marcap)
        # Note: Column names might vary slightly by version, checking common ones
        cols = ['Code', 'Name', 'Market', 'Marcap']
        
        df = pd.concat([kospi[cols], kosdaq[cols]])
        
        # Sort by Market Cap descending
        df['Marcap'] = pd.to_numeric(df['Marcap'], errors='coerce')
        df = df.sort_values('Marcap', ascending=False)
        
        print(f"Total stocks found: {len(df)}")
        
        # Save Metadata
        df.to_csv(os.path.join(DATA_DIR, 'ticker_metadata.csv'), index=False)
        print("Saved ticker_metadata.csv")
        
        return df
    except Exception as e:
        print(f"Error fetching stock lists: {e}")
        return pd.DataFrame()

def fetch_prices(stock_list):
    """Fetch daily prices for stocks in the list."""
    all_data = []
    
    # helper for progress bar
    total = len(stock_list)
    if LIMIT:
        total = min(total, LIMIT)
        stock_list = stock_list.head(LIMIT)
        print(f"Limiting to top {LIMIT} stocks for demo purposes.")
    
    print(f"Fetching price data from {START_DATE}...")
    
    for _, row in tqdm(stock_list.iterrows(), total=total):
        code = row['Code']
        name = row['Name']
        try:
            # Fetch daily data
            df = fdr.DataReader(code, START_DATE)
            
            if df.empty:
                continue
                
            df = df.reset_index()
            
            # Normalize columns
            # FDR returns: Date, Open, High, Low, Close, Volume, Change
            df = df.rename(columns={
                'Date': 'time',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Add metadata
            df['ticker'] = code
            
            # Format date string
            df['time'] = df['time'].dt.strftime('%Y-%m-%d')
            
            # Select required columns
            df = df[['ticker', 'time', 'open', 'high', 'low', 'close', 'volume']]
            
            all_data.append(df)
            
        except Exception as e:
            print(f"Error fetching {code} ({name}): {e}")
            continue
            
    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        return master_df
    else:
        return pd.DataFrame()

def generate_ticker_map(stock_list):
    """Generate mapping for yfinance fallback."""
    mapping = []
    for _, row in stock_list.iterrows():
        code = row['Code']
        market = row['Market']
        # KOSPI -> .KS, KOSDAQ -> .KQ
        suffix = '.KS' if market == 'KOSPI' else '.KQ'
        mapping.append({'ticker': code, 'yahoo_ticker': f"{code}{suffix}"})
    
    map_df = pd.DataFrame(mapping)
    map_df.to_csv(os.path.join(DATA_DIR, 'ticker_to_yahoo_map.csv'), index=False)
    print("Generated ticker_to_yahoo_map.csv")

def main():
    # 1. Get List
    stocks = get_stock_list()
    if stocks.empty:
        print("No stocks found. Exiting.")
        return

    # 2. Generate Map
    generate_ticker_map(stocks)
    
    # 3. Fetch Prices
    price_data = fetch_prices(stocks)
    
    # 4. Save
    if not price_data.empty:
        price_data.to_csv(PRICES_FILE, index=False)
        print(f"Successfully saved {len(price_data)} rows to {PRICES_FILE}")
    else:
        print("No price data collected.")

if __name__ == "__main__":
    main()
