import os
import json
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import threading
import subprocess
import traceback
import yfinance as yf

app = Flask(__name__)

# --- Configuration ---
DATA_DIR = '.'
ANALYSIS_FILE = 'wave_transition_analysis_results.csv'
PRICES_FILE = 'daily_prices.csv'
HISTORY_FILE = 'recommendation_history.csv'

# Ticker Mapping (Simple fallback, ideally load from a file)
TICKER_TO_YAHOO_MAP = {}
# Load map if exists
if os.path.exists('ticker_to_yahoo_map.csv'):
    try:
        map_df = pd.read_csv('ticker_to_yahoo_map.csv', dtype=str)
        TICKER_TO_YAHOO_MAP = dict(zip(map_df['ticker'], map_df['yahoo_ticker']))
    except:
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/portfolio')
def get_portfolio_data():
    try:
        # Load Analysis Results
        if not os.path.exists(ANALYSIS_FILE):
            return jsonify({'error': 'Analysis file not found. Please run analysis first.'})
        
        df = pd.read_csv(ANALYSIS_FILE, dtype={'ticker': str})
        df['ticker'] = df['ticker'].apply(lambda x: str(x).zfill(6))
        
        # Load History for Return Calculation
        history_df = pd.DataFrame()
        if os.path.exists(HISTORY_FILE):
            history_df = pd.read_csv(HISTORY_FILE, dtype={'ticker': str})
            history_df['ticker'] = history_df['ticker'].apply(lambda x: str(x).zfill(6))

        # --- Top Holdings (S & A Grade) ---
        top_picks = df[df['investment_grade'].isin(['S', 'A'])].copy()
        
        # Sort by Score
        top_picks = top_picks.sort_values('final_investment_score', ascending=False)
        
        top_holdings = []
        for _, row in top_picks.iterrows():
            # Calculate Return if in history
            rec_price = float(row['current_price']) # Default to current if not found
            if not history_df.empty:
                hist_row = history_df[history_df['ticker'] == row['ticker']]
                if not hist_row.empty:
                    rec_price = float(hist_row.iloc[-1]['entry_price']) # Use entry price for return calc
            
            cur_price = float(row['current_price'])
            return_pct = ((cur_price - rec_price) / rec_price * 100) if rec_price > 0 else 0.0

            top_holdings.append({
                'ticker': row['ticker'],
                'name': row['name'],
                'price': cur_price,
                'recommendation_price': rec_price,
                'return_pct': return_pct,
                'score': float(row['final_investment_score']),
                'grade': row['investment_grade'],
                'wave': int(row['wave_stage']) if pd.notna(row['wave_stage']) else 0,
                'sd_stage': row['supply_demand_stage'],
                'inst_trend': row.get('institutional_trend', 'N/A'),
                'ytd': float(row.get('price_change_20d', 0)) * 100 # Using 20d change as proxy
            })

        # --- Market Indices ---
        market_indices = []
        indices_map = {
            'KRW=X': 'USD/KRW',
            '^KS11': 'KOSPI',
            '^KQ11': 'KOSDAQ',
            '^IXIC': 'NASDAQ',
            '^GSPC': 'S&P 500',
            'DX-Y.NYB': 'Dollar Index'
        }
        
        try:
            tickers_list = list(indices_map.keys())
            idx_data = yf.download(tickers_list, period='5d', progress=False, threads=True)
            
            if not idx_data.empty:
                closes = idx_data['Close']
                for ticker, name in indices_map.items():
                    try:
                        if isinstance(closes, pd.DataFrame) and ticker in closes.columns:
                            series = closes[ticker].dropna()
                        elif isinstance(closes, pd.Series) and closes.name == ticker:
                            series = closes.dropna()
                        else:
                            continue
                            
                        if len(series) >= 2:
                            current_val = series.iloc[-1]
                            prev_val = series.iloc[-2]
                            change = current_val - prev_val
                            change_pct = (change / prev_val) * 100
                            
                            market_indices.append({
                                'name': name,
                                'price': f"{current_val:,.2f}",
                                'change': f"{change:,.2f}",
                                'change_pct': change_pct,
                                'color': 'red' if change >= 0 else 'blue'
                            })
                    except:
                        continue
        except Exception as e:
            print(f"Error fetching indices: {e}")

        # --- Style Box (Dynamic Calculation) ---
        style_box = {
            'large_growth': 0, 'large_core': 0, 'large_value': 0,
            'mid_growth': 0, 'mid_core': 0, 'mid_value': 0,
            'small_growth': 0, 'small_core': 0, 'small_value': 0
        }
        
        if 'market_cap_size' in df.columns and 'investment_style' in df.columns:
            # Count occurrences
            counts = df.groupby(['market_cap_size', 'investment_style']).size()
            total_count = len(df)
            
            if total_count > 0:
                for size in ['Large', 'Mid', 'Small']:
                    for style in ['Growth', 'Core', 'Value']:
                        key = f"{size.lower()}_{style.lower()}"
                        # Check if exists in counts
                        if (size, style) in counts.index:
                            style_box[key] = int((counts[(size, style)] / total_count) * 100)
        else:
             # Fallback if columns missing
             style_box = {'large_growth': 20, 'large_core': 20, 'large_value': 10, 
                          'mid_growth': 10, 'mid_core': 10, 'mid_value': 10,
                          'small_growth': 10, 'small_core': 5, 'small_value': 5}

        return jsonify({
            'market_indices': market_indices,
            'top_holdings': top_holdings,
            'style_box': style_box,
            'latest_date': datetime.now().strftime('%Y-%m-%d')
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<ticker>')
def get_stock_detail(ticker):
    ticker = str(ticker).zfill(6)
    try:
        # 1. Metrics from Analysis
        metrics = {}
        if os.path.exists(ANALYSIS_FILE):
            df = pd.read_csv(ANALYSIS_FILE, dtype={'ticker': str})
            df['ticker'] = df['ticker'].apply(lambda x: str(x).zfill(6))
            row = df[df['ticker'] == ticker]
            if not row.empty:
                r = row.iloc[0]
                metrics = {
                    'name': r['name'],
                    'score': float(r['final_investment_score']),
                    'grade': r['investment_grade'],
                    'wave_stage': int(r['wave_stage']) if pd.notna(r['wave_stage']) else 0,
                    'supply_demand': r['supply_demand_stage']
                }

        # 2. Price History (Fetch from local CSV first, fallback to yfinance)
        price_history = []
        if os.path.exists(PRICES_FILE):
             try:
                # Optimized reading: read all and filter (for prototype) or read filtered
                # For this scale, reading full CSV is fine.
                p_df = pd.read_csv(PRICES_FILE, dtype={'ticker': str})
                p_df = p_df[p_df['ticker'] == ticker].copy()
                
                if not p_df.empty:
                    # Sort by time
                    p_df['time'] = pd.to_datetime(p_df['time'])
                    p_df.sort_values('time', inplace=True)
                    
                    for _, row in p_df.iterrows():
                        price_history.append({
                            'time': row['time'].strftime('%Y-%m-%d'),
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'volume': int(row['volume'])
                        })
             except Exception as e:
                 print(f"Error reading local CSV: {e}")

        # Fallback to Yahoo Finance if local data is empty
        if not price_history:
            try:
                yf_ticker = TICKER_TO_YAHOO_MAP.get(ticker, f"{ticker}.KS")
                stock = yf.Ticker(yf_ticker)
                hist = stock.history(period="5y")
                
                if not hist.empty:
                    hist = hist.reset_index()
                    for _, row in hist.iterrows():
                        date_val = row['Date']
                        date_str = date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val).split(' ')[0]
                        price_history.append({
                            'time': date_str,
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume'])
                        })
            except Exception as e:
                print(f"Error fetching yfinance: {e}")

        return jsonify({
            'metrics': metrics,
            'price_history': price_history
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    def run_scripts():
        # Using uv run to execute in the environment
        subprocess.run(['uv', 'run', 'analysis2.py'], check=True)
        subprocess.run(['uv', 'run', 'track_performance.py'], check=True)
    
    threading.Thread(target=run_scripts).start()
    return jsonify({'status': 'started'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
