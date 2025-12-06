import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_random_price_history(ticker, name, start_price, days=365):
    """
    Generates a realistic-looking daily price history with trends and noise.
    """
    dates = []
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    
    current_price = start_price
    start_date = datetime.now() - timedelta(days=days)
    
    # Random trend factor (some stocks go up, some down)
    trend = random.uniform(-0.0005, 0.0005) 
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        if date.weekday() >= 5: # Skip weekends
            continue
            
        # Daily volatility
        change_pct = np.random.normal(trend, 0.02) # Mean=trend, Std=2%
        
        open_price = current_price * (1 + np.random.normal(0, 0.005))
        close_price = current_price * (1 + change_pct)
        
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
        
        volume = int(np.random.normal(1000000, 200000))
        volume = max(10000, volume)
        
        dates.append(date.strftime('%Y-%m-%d'))
        opens.append(int(open_price))
        highs.append(int(high_price))
        lows.append(int(low_price))
        closes.append(int(close_price))
        volumes.append(volume)
        
        current_price = close_price
        
        # Periodic trend change (every ~60 days)
        if i % 60 == 0:
            trend = random.uniform(-0.001, 0.001)

    df = pd.DataFrame({
        'ticker': ticker,
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })
    return df

def main():
    tickers = [
        ('005930', 'Samsung Electronics', 70000),
        ('000660', 'SK Hynix', 120000),
        ('035420', 'NAVER', 200000),
        ('005380', 'Hyundai Motor', 180000),
        ('000270', 'Kia', 80000),
        ('006400', 'Samsung SDI', 450000),
        ('051910', 'LG Chem', 600000),
        ('068270', 'Celltrion', 160000),
        ('035720', 'Kakao', 50000),
        ('105560', 'KB Financial', 55000),
    ]
    
    all_data = []
    for ticker, name, price in tickers:
        print(f"Generating data for {name} ({ticker})...")
        df = generate_random_price_history(ticker, name, price)
        all_data.append(df)
        
    final_df = pd.concat(all_data)
    final_df.sort_values(['ticker', 'date'], inplace=True)
    
    output_file = 'daily_prices.csv'
    final_df.to_csv(output_file, index=False)
    print(f"Saved {len(final_df)} rows to {output_file}")

if __name__ == "__main__":
    main()
