# Domestic Stock Analysis System - Master Blueprint

This document provides a complete guide to recreating the Domestic Stock Analysis System on **Windows 11** using the **uv** package manager. It includes the project overview, file structure, setup instructions, and the full source code for all critical components.

## 1. Project Overview

**Goal**: A web-based dashboard for analyzing Korean stocks (KOSPI/KOSDAQ) using technical analysis (Wave Theory), market regime detection, and AI-driven recommendations.

**Tech Stack**:
-   **Backend**: Python, Flask, Pandas, yfinance
-   **Frontend**: HTML5, Tailwind CSS, Lightweight Charts (TradingView), JavaScript
-   **Data**: Naver Finance (via scraping), Yahoo Finance (yfinance)
-   **Analysis**: Custom Wave Theory implementation, Moving Averages, RSI, MACD
-   **Package Manager**: `uv` (Fast Python package installer and resolver)

## 2. File Structure

Create the following directory structure:

```
project_root/
├── .venv/                        # (Generated) Virtual Environment
├── pyproject.toml                # (Generated) Project configuration & dependencies
├── uv.lock                       # (Generated) Dependency lock file
├── analysis2.py                  # Core analysis logic (Wave Theory, Technicals)
├── create_complete_daily_prices.py # Data collection script (Naver Finance)
├── flask_app.py                  # Web server (Flask)
├── track_performance.py          # Performance tracking script
├── templates/
│   └── index.html                # Dashboard frontend
├── daily_prices.csv              # (Generated) Historical price data
├── recommendation_history.csv    # (Generated) Past recommendations
└── wave_transition_analysis_results.csv # (Generated) Latest analysis results
```

## 3. Setup Instructions (Windows 11 & uv)

### 3.1. Install `uv`
Open **PowerShell** as Administrator (or standard user) and run:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

*Note: You may need to restart your terminal after installation.*

### 3.2. Initialize Project

1.  **Create Project Folder**:
    ```powershell
    mkdir stock_analysis
    cd stock_analysis
    mkdir templates
    ```

2.  **Initialize with uv**:
    ```powershell
    uv init
    ```
    This creates `pyproject.toml` and `.python-version`.

3.  **Add Dependencies**:
    Run the following command to add all required libraries. `uv` will automatically create the virtual environment and install them.

    ```powershell
    uv add flask gunicorn yfinance pandas numpy requests tqdm python-dotenv plotly google-generativeai duckduckgo-search newspaper3k lxml_html_clean beautifulsoup4
    ```

### 3.3. Create Source Files
Copy the code provided in **Section 4** into the respective files in your project directory:
-   `flask_app.py`
-   `create_complete_daily_prices.py`
-   `analysis2.py`
-   `track_performance.py`
-   `templates/index.html`

### 3.4. Initialize Data
Run the data collection script to fetch historical prices. Using `uv run` executes the script within the project's virtual environment automatically.

```powershell
uv run create_complete_daily_prices.py
```

### 3.5. Run Analysis
Generate the initial analysis results:

```powershell
uv run analysis2.py
```

### 3.6. Start Dashboard
Run the Flask server:

```powershell
uv run flask_app.py
```

Open your browser to [http://localhost:5001](http://localhost:5001).

---

## 4. Source Code

### 4.1. flask_app.py

```python
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
                    rec_price = float(hist_row.iloc[-1]['current_price']) # Use last recommendation price
            
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
                'wave': row['wave_stage'],
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

        # --- Style Box (Approximation) ---
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
                    'wave_stage': r['wave_stage'],
                    'supply_demand': r['supply_demand_stage']
                }

        # 2. Price History (Fetch 5Y from yfinance)
        price_history = []
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
```

### 4.2. templates/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Analysis Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: 'Inter', sans-serif; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #1a1a1a; }
        ::-webkit-scrollbar-thumb { background: #333; rounded: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #444; }
    </style>
</head>
<body class="h-screen flex flex-col overflow-hidden">
    <!-- Header -->
    <header class="h-14 border-b border-[#2a2a2a] flex items-center px-4 justify-between bg-[#1a1a1a]">
        <div class="flex items-center gap-2">
            <span class="text-xl font-bold text-blue-500">ANTIGRAVITY</span>
            <span class="text-xs text-gray-500 px-2 py-0.5 border border-[#333] rounded">BETA</span>
        </div>
        <button onclick="triggerAnalysis()" class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-sm transition-colors">
            Run Analysis
        </button>
    </header>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto p-4 bg-[#121212]">
        <!-- Market Indices -->
        <section class="mb-6">
            <h2 class="text-sm font-bold text-gray-300 mb-2">Market Indices</h2>
            <div id="market-indices-container" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <!-- Populated by JS -->
            </div>
        </section>

        <div class="grid grid-cols-12 gap-6">
            <!-- Chart Section (Left) -->
            <div class="col-span-12 lg:col-span-8 flex flex-col gap-6">
                <div class="flex-1 min-h-[400px] border border-[#2a2a2a] rounded p-4 relative flex flex-col">
                    <div class="flex items-center justify-between mb-2">
                        <div>
                            <h2 class="text-sm font-bold text-gray-300">Price Chart</h2>
                            <span id="summary-chart-ticker" class="text-xs text-blue-400 font-mono ml-2"></span>
                        </div>
                        <div class="flex items-center gap-1 bg-[#1a1a1a] rounded p-0.5 border border-[#333]">
                            <button onclick="setChartRange('1D')" class="chart-range-btn px-2 py-0.5 text-[10px] font-medium text-gray-400 hover:text-white hover:bg-[#333] rounded" data-range="1D">1D</button>
                            <button onclick="setChartRange('1W')" class="chart-range-btn px-2 py-0.5 text-[10px] font-medium text-gray-400 hover:text-white hover:bg-[#333] rounded" data-range="1W">1W</button>
                            <button onclick="setChartRange('1M')" class="chart-range-btn px-2 py-0.5 text-[10px] font-medium text-gray-400 hover:text-white hover:bg-[#333] rounded" data-range="1M">1M</button>
                            <button onclick="setChartRange('3M')" class="chart-range-btn px-2 py-0.5 text-[10px] font-medium text-gray-400 hover:text-white hover:bg-[#333] rounded" data-range="3M">3M</button>
                            <button onclick="setChartRange('6M')" class="chart-range-btn px-2 py-0.5 text-[10px] font-medium text-gray-400 hover:text-white hover:bg-[#333] rounded" data-range="6M">6M</button>
                            <button onclick="setChartRange('1Y')" class="chart-range-btn px-2 py-0.5 text-[10px] font-medium text-white bg-[#333] rounded" data-range="1Y">1Y</button>
                            <button onclick="setChartRange('5Y')" class="chart-range-btn px-2 py-0.5 text-[10px] font-medium text-gray-400 hover:text-white hover:bg-[#333] rounded" data-range="5Y">5Y</button>
                            <button onclick="setChartRange('All')" class="chart-range-btn px-2 py-0.5 text-[10px] font-medium text-gray-400 hover:text-white hover:bg-[#333] rounded" data-range="All">All</button>
                        </div>
                    </div>
                    <div id="summary-chart-container" class="flex-1 w-full relative"></div>
                </div>
            </div>

            <!-- Recommendations List (Right) -->
            <div class="col-span-12 lg:col-span-4 flex flex-col gap-6">
                <div class="bg-[#1a1a1a] border border-[#2a2a2a] rounded p-4 h-full overflow-hidden flex flex-col">
                    <h2 class="text-sm font-bold text-gray-300 mb-4">AI Recommendations</h2>
                    <div class="overflow-auto flex-1">
                        <table class="w-full text-left border-collapse">
                            <thead class="text-xs text-gray-500 border-b border-[#333] sticky top-0 bg-[#1a1a1a]">
                                <tr>
                                    <th class="p-2">Ticker</th>
                                    <th class="p-2 text-right">Price</th>
                                    <th class="p-2 text-right">Return</th>
                                    <th class="p-2 text-center">Grade</th>
                                </tr>
                            </thead>
                            <tbody id="holdings-table-body" class="text-sm text-gray-300"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let summaryChart;
        let summaryCandleSeries;
        let summaryVolumeSeries;
        let currentChartData = { candles: [], volumes: [] };
        let currentRange = '1Y';

        async function updateDashboard() {
            try {
                const response = await fetch('/api/portfolio');
                const data = await response.json();
                
                if (data.market_indices) renderMarketIndices(data.market_indices);
                if (data.top_holdings) {
                    renderHoldingsTable(data.top_holdings);
                    if (data.top_holdings.length > 0) {
                        updateSummaryChart(data.top_holdings[0].ticker);
                    }
                }
            } catch (e) {
                console.error("Error:", e);
            }
        }

        function renderMarketIndices(indices) {
            const container = document.getElementById('market-indices-container');
            container.innerHTML = indices.map(idx => {
                const colorClass = idx.color === 'red' ? 'text-[#FF4560]' : 'text-[#2962FF]';
                return `
                    <div class="bg-[#1a1a1a] border border-[#2a2a2a] rounded p-3 flex flex-col items-center justify-center hover:bg-[#252525] transition-colors">
                        <span class="text-xs text-gray-400 mb-1">${idx.name}</span>
                        <span class="text-lg font-bold text-white mb-1">${idx.price}</span>
                        <span class="text-xs font-medium ${colorClass}">${idx.change} (${idx.change_pct.toFixed(2)}%)</span>
                    </div>`;
            }).join('');
        }

        function renderHoldingsTable(holdings) {
            const tbody = document.getElementById('holdings-table-body');
            tbody.innerHTML = holdings.map(stock => {
                const returnColor = stock.return_pct >= 0 ? 'text-red-400' : 'text-blue-400';
                return `
                    <tr class="border-b border-gray-800 hover:bg-gray-800 cursor-pointer" onclick="updateSummaryChart('${stock.ticker}')">
                        <td class="p-2">
                            <div class="font-bold text-white">${stock.name}</div>
                            <div class="text-xs text-gray-500">${stock.ticker}</div>
                        </td>
                        <td class="p-2 text-right">${stock.price.toLocaleString()}</td>
                        <td class="p-2 text-right ${returnColor}">${stock.return_pct.toFixed(1)}%</td>
                        <td class="p-2 text-center">
                            <span class="px-2 py-0.5 rounded bg-blue-900 text-blue-200 text-xs">${stock.grade}</span>
                        </td>
                    </tr>`;
            }).join('');
        }

        async function updateSummaryChart(ticker) {
            const container = document.getElementById('summary-chart-container');
            container.innerHTML = ''; // Clear
            
            try {
                const response = await fetch(`/api/stock/${ticker}`);
                const data = await response.json();
                
                document.getElementById('summary-chart-ticker').innerText = data.metrics.name || ticker;
                
                currentChartData.candles = data.price_history;
                currentChartData.volumes = data.price_history.map(d => ({ time: d.time, value: d.volume }));

                summaryChart = LightweightCharts.createChart(container, {
                    layout: { background: { color: '#121212' }, textColor: '#D1D5DB' },
                    grid: { vertLines: { color: '#2a2a2a' }, horzLines: { color: '#2a2a2a' } },
                    width: container.clientWidth,
                    height: container.clientHeight,
                    handleScroll: false,
                    handleScale: false,
                });

                summaryCandleSeries = summaryChart.addCandlestickSeries({
                    upColor: '#EF4444', downColor: '#3B82F6', borderVisible: false, wickUpColor: '#EF4444', wickDownColor: '#3B82F6',
                });
                summaryVolumeSeries = summaryChart.addHistogramSeries({
                    color: '#26a69a', priceFormat: { type: 'volume' }, priceScaleId: '',
                });
                summaryChart.priceScale('').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

                setChartRange(currentRange);

                new ResizeObserver(entries => {
                    if (entries[0].contentRect) {
                        summaryChart.applyOptions({ width: entries[0].contentRect.width, height: entries[0].contentRect.height });
                    }
                }).observe(container);

            } catch (e) {
                console.error("Chart Error:", e);
            }
        }

        function setChartRange(range) {
            currentRange = range;
            document.querySelectorAll('.chart-range-btn').forEach(btn => {
                if (btn.dataset.range === range) {
                    btn.classList.add('text-white', 'bg-[#333]');
                    btn.classList.remove('text-gray-400');
                } else {
                    btn.classList.remove('text-white', 'bg-[#333]');
                    btn.classList.add('text-gray-400');
                }
            });

            if (summaryChart && currentChartData.candles.length > 0) {
                const filtered = filterDataByRange(currentChartData.candles, currentChartData.volumes, range);
                summaryCandleSeries.setData(filtered.candles);
                summaryVolumeSeries.setData(filtered.volumes);
                summaryChart.timeScale().fitContent();
            }
        }

        function filterDataByRange(candles, volumes, range) {
            if (!candles || candles.length === 0) return { candles: [], volumes: [] };
            if (range === 'All') return { candles, volumes };

            const lastCandleTime = candles[candles.length - 1].time;
            const lastDate = new Date(lastCandleTime);
            let startDate = new Date(lastDate);

            switch (range) {
                case '1D': startDate.setDate(lastDate.getDate() - 1); break;
                case '1W': startDate.setDate(lastDate.getDate() - 7); break;
                case '1M': startDate.setMonth(lastDate.getMonth() - 1); break;
                case '3M': startDate.setMonth(lastDate.getMonth() - 3); break;
                case '6M': startDate.setMonth(lastDate.getMonth() - 6); break;
                case '1Y': startDate.setFullYear(lastDate.getFullYear() - 1); break;
                case '5Y': startDate.setFullYear(lastDate.getFullYear() - 5); break;
            }

            const startTime = startDate.getTime();
            const filteredCandles = candles.filter(d => new Date(d.time).getTime() >= startTime);
            const filteredVolumes = volumes.filter(d => new Date(d.time).getTime() >= startTime);

            return { candles: filteredCandles, volumes: filteredVolumes };
        }

        async function triggerAnalysis() {
            if (confirm("Run new analysis? This may take a few minutes.")) {
                await fetch('/api/run-analysis', { method: 'POST' });
                alert("Analysis started in background.");
            }
        }

        // Init
        updateDashboard();
    </script>
</body>
</html>
```

### 4.3. analysis2.py & create_complete_daily_prices.py

*(Note: Ensure you copy the full content of these files from your original project.)*

## 5. Usage (Routine Operations)

1.  **Data Update**:
    Run this daily after market close (15:30 KST):
    ```powershell
    uv run create_complete_daily_prices.py
    ```

2.  **Analysis**:
    Run this to generate new recommendations:
    ```powershell
    uv run analysis2.py
    ```

3.  **Dashboard**:
    Start the dashboard server:
    ```powershell
    uv run flask_app.py
    ```
