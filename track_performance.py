import pandas as pd
import os
from datetime import datetime

# Configuration
DATA_DIR = '.'
ANALYSIS_FILE = os.path.join(DATA_DIR, 'wave_transition_analysis_results.csv')
HISTORY_FILE = os.path.join(DATA_DIR, 'recommendation_history.csv')
PRICES_FILE = os.path.join(DATA_DIR, 'daily_prices.csv')

def load_data():
    """Lengths dataframes."""
    if not os.path.exists(ANALYSIS_FILE):
        print("Analysis file not found.")
        return None, None, None
    
    analysis_df = pd.read_csv(ANALYSIS_FILE, dtype={'ticker': str})
    
    if os.path.exists(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE, dtype={'ticker': str})
    else:
        history_df = pd.DataFrame(columns=['ticker', 'name', 'entry_date', 'entry_price', 'current_price', 'return_pct', 'grade', 'status'])

    daily_prices = pd.DataFrame()
    if os.path.exists(PRICES_FILE):
        daily_prices = pd.read_csv(PRICES_FILE, dtype={'ticker': str})
        
    return analysis_df, history_df, daily_prices

def get_latest_price(ticker, daily_prices):
    """Get latest close price for a ticker."""
    if daily_prices.empty:
        return 0
    
    stock_prices = daily_prices[daily_prices['ticker'] == ticker]
    if stock_prices.empty:
        return 0
        
    # Assuming daily_prices is sorted or we verify the latest date
    # But usually creating complete daily prices sorts it? 
    # Let's ensure sort by time
    stock_prices = stock_prices.sort_values('time')
    return float(stock_prices.iloc[-1]['close'])

def update_performance():
    analysis_df, history_df, daily_prices = load_data()
    
    if analysis_df is None:
        return

    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Identify New High-Conviction Picks (S or A Grade)
    top_picks = analysis_df[analysis_df['investment_grade'].isin(['S', 'A'])]
    
    for _, row in top_picks.iterrows():
        ticker = row['ticker']
        name = row['name']
        current_grade = row['investment_grade']
        current_price = row['current_price']
        
        # Check if already in history as "Active"
        existing_active = history_df[(history_df['ticker'] == ticker) & (history_df['status'] == 'Active')]
        
        if existing_active.empty:
            # New Entry
            new_entry = {
                'ticker': ticker,
                'name': name,
                'entry_date': today_str,
                'entry_price': current_price,
                'current_price': current_price,
                'return_pct': 0.0,
                'grade': current_grade,
                'status': 'Active'
            }
            history_df = pd.concat([history_df, pd.DataFrame([new_entry])], ignore_index=True)
            print(f"New Entry: {name} ({ticker}) at {current_price}")
        else:
            # Update existing active position metrics (Grade change etc)
            idx = existing_active.index[0]
            history_df.at[idx, 'grade'] = current_grade # Update grade if changed (A -> S)
            # Price update happens below for ALL active positions

    # 2. Update Current Prices and Returns for ALL Active Positions
    # (Even if they are no longer in top_picks, we track them until we decide to close)
    # Ideally we should have an exit strategy (e.g. Grade drops to C), but for now we just track.
    
    for idx, row in history_df.iterrows():
        if row['status'] == 'Active':
            ticker = row['ticker']
            
            # Get latest price from daily_prices (more accurate than analysis file if run separately)
            # Or use analysis file price if available
            latest_price = 0
            
            # Try getting from analysis df first (most up to date context)
            analysis_row = analysis_df[analysis_df['ticker'] == ticker]
            if not analysis_row.empty:
                latest_price = float(analysis_row.iloc[0]['current_price'])
            else:
                # Fallback to prices file
                latest_price = get_latest_price(ticker, daily_prices)
            
            if latest_price > 0:
                entry_price = float(row['entry_price'])
                return_pct = ((latest_price - entry_price) / entry_price) * 100
                
                history_df.at[idx, 'current_price'] = latest_price
                history_df.at[idx, 'return_pct'] = round(return_pct, 2)
                
                # Simple Exit Logic: If Grade drops to B or C in analysis, mark as Closed?
                # For now let's keep it simple: Just update returns.
                
                # Check for "Exit" condition (Drop out of recommended list completely or Grade C)
                # This is a bit tricky without a proper portfolio manager logic.
                # For this task, "Tracking" is sufficient.

    # 3. Save
    history_df.to_csv(HISTORY_FILE, index=False)
    print(f"Performance history updated. Total records: {len(history_df)}")
    print(history_df.tail())

if __name__ == "__main__":
    update_performance()
