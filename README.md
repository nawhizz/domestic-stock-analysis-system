# 국내 주식 발굴 및 분석 대시보드 (Domestic Stock Analysis System)

**Python + Flask + Tailwind CSS** 기반의 국내 주식(KOSPI, KOSDAQ) 자동 분석 및 시각화 시스템입니다.
Wave Theory(파동 이론)와 Market Regime(시장 체제) 분석을 통해 유망 종목을 발굴하고, 웹 대시보드를 통해 직관적으로 시각화합니다.


## 🚀 주요 기능 (Key Features)

1.  **전체 시장 스캔 (Full Market Scan)**
    - FinanceDataReader를 이용하여 **KOSPI & KOSDAQ 전 종목(약 2,500개)**의 2년치 데이터를 수집 및 분석합니다.
    - 시가총액(Large/Mid/Small) 및 종목 메타데이터 자동 맵핑.

2.  **고급 분석 알고리즘 (Analysis Engine)**
    - **Markret Regime**: 이동평균선(MA20, 60, 120) 정배열/역배열 기반 시장 국면 파악.
    - **Wave Theory**: Higher Highs/Lows 로직을 통한 상승 파동(Impulse Wave) 및 조정 파동 식별.
    - **Technical Indicators**: RSI, MACD, Volume Profile 등을 활용한 종합 점수 산출 (S/A/B/C 등급).
    - **Style Box Proxy**: 가격 모멘텀과 시가총액을 결합하여 스타일(Growth/Value/Core) 자동 분류.

3.  **대시보드 (Web Dashboard)**
    - **Interactive Charts**: Lightweight Charts를 활용한 고성능 반응형 차트.
    - **AI Recommendations**: S/A 등급 유망 종목 리스트 제공.
    - **Portfolio Style Box**: 시장 전체의 추천 종목 분포(Large-Growth 등) 시각화.
    - **Dark Mode UI**: 눈이 편안한 다크 모드 기반의 프리미엄 UI.

4.  **수익률 추적 (Performance Tracking)**
    - 추천 시점(S/A등급 진입)의 가격을 기록하고, 현재가 대비 수익률을 자동으로 추적 관리.

---

## 🛠️ 기술 스택 (Tech Stack)

-   **Language**: Python 3.12+
-   **Package Manager**: `uv` (Fast Python package installer)
-   **Web Framework**: Flask
-   **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS (CDN), Lightweight Charts
-   **Data Analysis**: Pandas, NumPy, FinanceDataReader, yfinance
-   **Database**: CSV Files (File-based system for portability)

---

## ⚙️ 설치방법 (Installation)

이 프로젝트는 `uv`를 패키지 매니저로 사용합니다.

1.  **Repository Clone**
    ```bash
    git clone <repository-url>
    cd domestic-stock-analysis-system
    ```

2.  **의존성 설치 (Install Dependencies)**
    ```bash
    uv sync
    ```

---

## 🖥️ 사용방법 (Usage Guide)

데이터 수집부터 분석, 대시보드 실행까지 다음 3단계를 순서대로 진행하세요.

### Step 1. 데이터 수집 (Data Collection)
KOSPI/KOSDAQ 전 종목의 데이터를 수집합니다. (약 10~20분 소요)
```bash
uv run create_complete_daily_prices.py
```
* 결과물: `daily_prices.csv`, `ticker_metadata.csv`, `ticker_to_yahoo_map.csv`

### Step 2. 데이터 분석 (Analysis)
수집된 데이터를 바탕으로 파동 분석 및 등급 산정을 수행합니다.
```bash
uv run analysis2.py
```
* 결과물: `wave_transition_analysis_results.csv` (분석 결과)

### Step 3. 성과 추적 및 대시보드 실행 (Run Dashboard)
수익률 트래킹을 업데이트하고 웹 서버를 실행합니다.
```bash
uv run track_performance.py
uv run flask_app.py
```
* **브라우저 접속**: [http://localhost:5001](http://localhost:5001)

---

## 📂 프로젝트 구조 (Structure)

```
domestic-stock-analysis-system/
├── analysis2.py                     # 핵심 분석 로직 (Wave, Regime, Scoring)
├── create_complete_daily_prices.py  # 데이터 수집 스크립트 (FinanceDataReader)
├── track_performance.py             # 수익률 추적 스크립트
├── flask_app.py                     # Flask 웹 서버 및 API
├── templates/
│   └── index.html                   # 프론트엔드 대시보드 (Tailwind + JS)
├── daily_prices.csv                 # [Data] 일별 주가 데이터 (Large File)
├── ticker_metadata.csv              # [Data] 종목 코드/이름/시총 정보
├── wave_transition_analysis_results # [Data] 분석 결과 파일
├── recommendation_history.csv       # [Data] 추천 이력 및 수익률 기록
├── pyproject.toml                   # 의존성 관리 설정
└── README.md                        # 프로젝트 문서
```

---

## 📝 License

This project is for educational purposes.
