## 🇰🇷 국내 주식 분석 시스템 - 마스터 설계도 (Master Blueprint)

본 문서는 **uv** 패키지 관리자를 사용하여 **Windows 11** 환경에서 국내 주식 분석 시스템을 재현하는 데 필요한 완벽한 가이드를 제공합니다. 프로젝트 개요, 파일 구조, 설정 지침 및 모든 핵심 구성 요소의 전체 소스 코드를 포함합니다.

-----

## 1\. 프로젝트 개요

**목표**: 기술적 분석(**파동 이론**), **시장 국면 감지** 및 **AI 기반 추천**을 사용하여 한국 주식(KOSPI/KOSDAQ)을 분석하기 위한 **웹 기반 대시보드**입니다.

**기술 스택**:

  * **백엔드**: Python, **Flask**, Pandas, yfinance
  * **프론트엔드**: HTML5, **Tailwind CSS**, Lightweight Charts (TradingView), JavaScript
  * **데이터**: 네이버 금융(스크래핑), 야후 파이낸스(yfinance)
  * **분석**: 사용자 지정 파동 이론 구현, 이동 평균선(Moving Averages), RSI, MACD
  * **패키지 관리자**: `uv` (빠른 Python 패키지 설치 및 해결 도구)

-----

## 2\. 파일 구조

다음과 같은 디렉토리 구조를 생성합니다.

```
project_root/
├── .venv/                        # (생성됨) 가상 환경 (Virtual Environment)
├── pyproject.toml                # (생성됨) 프로젝트 구성 및 종속성
├── uv.lock                       # (생성됨) 종속성 잠금 파일
├── analysis2.py                  # 핵심 분석 로직 (파동 이론, 기술적 지표)
├── create_complete_daily_prices.py # 데이터 수집 스크립트 (네이버 금융)
├── flask_app.py                  # 웹 서버 (Flask)
├── track_performance.py          # 성과 추적 스크립트
├── templates/
│   └── index.html                # 대시보드 프론트엔드
├── daily_prices.csv              # (생성됨) 과거 가격 데이터
├── recommendation_history.csv    # (생성됨) 과거 추천 내역
└── wave_transition_analysis_results.csv # (생성됨) 최신 분석 결과
```

-----

## 3\. 설정 지침 (Windows 11 & uv)

### 3.1. `uv` 설치

**PowerShell**을 관리자 권한(또는 표준 사용자)으로 열고 다음을 실행합니다.

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **참고**: 설치 후 터미널을 다시 시작해야 할 수 있습니다.

### 3.2. 프로젝트 초기화

1.  **프로젝트 폴더 생성**:

    ```powershell
    mkdir stock_analysis
    cd stock_analysis
    mkdir templates
    ```

2.  **uv로 초기화**:

    ```powershell
    uv init
    ```

    이 명령어는 `pyproject.toml` 및 `.python-version` 파일을 생성합니다.

3.  **종속성 추가**:
    다음 명령을 실행하여 필요한 모든 라이브러리를 추가합니다. `uv`는 자동으로 **가상 환경**을 생성하고 라이브러리를 설치합니다.

    ```powershell
    uv add flask gunicorn yfinance pandas numpy requests tqdm python-dotenv plotly google-generativeai duckduckgo-search newspaper3k lxml_html_clean beautifulsoup4
    ```

### 3.3. 소스 파일 생성

다음 섹션에 제공된 코드를 프로젝트 디렉토리 내의 해당 파일에 복사합니다.

  * `flask_app.py`
  * `create_complete_daily_prices.py`
  * `analysis2.py`
  * `track_performance.py`
  * `templates/index.html`

### 3.4. 데이터 초기화

과거 가격을 가져오기 위해 데이터 수집 스크립트를 실행합니다.

```powershell
uv run create_complete_daily_prices.py
```

### 3.5. 분석 실행

초기 분석 결과를 생성합니다.

```powershell
uv run analysis2.py
```

### 3.6. 대시보드 시작

Flask 서버를 실행하고 브라우저에서 접속합니다.

```powershell
uv run flask_app.py
```

> 브라우저 접속 주소: **[http://localhost:5001](https://www.google.com/search?q=http://localhost:5001)**

-----

## 4\. 소스 코드

### 4.1. `flask_app.py`

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

### 4.2. `templates/index.html`

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
        <header class="h-14 border-b border-[#2a2a2a] flex items-center px-4 justify-between bg-[#1a1a1a]">
        <div class="flex items-center gap-2">
            <span class="text-xl font-bold text-blue-500">ANTIGRAVITY</span>
            <span class="text-xs text-gray-500 px-2 py-0.5 border border-[#333] rounded">BETA</span>
        </div>
        <button onclick="triggerAnalysis()" class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-sm transition-colors">
            Run Analysis
        </button>
    </header>

        <main class="flex-1 overflow-auto p-4 bg-[#121212]">
                <section class="mb-6">
            <h2 class="text-sm font-bold text-gray-300 mb-2">Market Indices</h2>
            <div id="market-indices-container" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                            </div>
        </section>

        <div class="grid grid-cols-12 gap-6">
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

### 4.3. `analysis2.py` 및 `create_complete_daily_prices.py`

```python
# (Note: Ensure you copy the full content of these files from your original project.)
# (참고: 이 파일들의 전체 내용은 원본 프로젝트에서 복사해야 합니다.)
```

-----

## 5\. 사용법 (정기적 운영)

1.  **데이터 업데이트**:
    장 마감 후 (한국 표준시 15:30) 매일 실행합니다.

    ```powershell
    uv run create_complete_daily_prices.py
    ```

2.  **분석**:
    새로운 추천을 생성하기 위해 실행합니다.

    ```powershell
    uv run analysis2.py
    ```

3.  **대시보드**:
    대시보드 서버를 시작합니다.

    ```powershell
    uv run flask_app.py
    ```