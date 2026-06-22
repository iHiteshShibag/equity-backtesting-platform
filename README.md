# 📈 Equity Backtesting Platform

End-to-end backtesting platform for testing fundamental-based equity strategies on Indian stock markets.

**Tech Stack:**

* Backend: Python + FastAPI + SQLAlchemy
* Database: PostgreSQL
* Frontend: React + Vite + Tailwind CSS + Recharts
* Data: yfinance (prices) + fundamentals via yfinance API

## Features

✅ **Backtest Engine**

* User-defined date ranges and rebalancing frequencies (monthly/quarterly/yearly)
* Portfolio sizing (top 20, 50, 100 stocks)
* Filtering: market cap range, ROCE threshold, PAT > 0
* Ranking: single/multi-metric ranking with custom ordering
* Position sizing: equal-weight, market-cap-weight, metric-weight
* No look-ahead bias in fundamentals
* Compounding logic at each rebalance

✅ **Data Layer**

* 100+ Indian listed companies (Nifty 100)
* Historical price data (OHLCV) from 2015+
* Fundamental data: P\&L, balance sheet, cash flow, and ratios (P/E, ROCE, ROE, PAT, etc.)

✅ **Analytics Dashboard**

* Equity curve visualization
* Drawdown analysis
* Benchmark CAGR comparison (Nifty 50)
* Alpha calculation vs benchmark
* Performance metrics: CAGR, Sharpe, Sortino, Max Drawdown, Calmar
* Rebalance logs with holdings and weights
* Top winners/losers stock list
* CSV/Excel export

\---

## Prerequisites

* **Python 3.11+** → [python.org](https://python.org)
* **Node.js 18+** → [nodejs.org](https://nodejs.org)
* **PostgreSQL 16** → [postgresql.org](https://postgresql.org/download)
* **Git** → [git-scm.com](https://git-scm.com)

\---

## Installation \& Setup

### Step 1: Database

```bash
# Create database
createdb backtesting\_db
```

### Step 2: Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\\Scripts\\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env with your PostgreSQL password:
# DATABASE\_URL=postgresql://postgres:YOUR\_PASSWORD@localhost:5432/backtesting\_db

# Create tables (using SQLAlchemy)
python -c "from app.database import engine, Base; from app.models import \*; Base.metadata.create\_all(bind=engine)"

# Fetch data (takes 5-10 minutes for first run)
python scripts/ingest\_data.py

# Start backend
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Step 3: Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
copy .env.example .env

# Start dev server
npm run dev
```

Frontend runs at `http://localhost:5173`

\---

## Usage

1. **Open** `http://localhost:5173` in your browser
2. **Configure backtest parameters:**

   * Date range (e.g., 2018-2024)
   * Rebalance frequency (monthly/quarterly/yearly)
   * Portfolio size (top 20, 50, 100 stocks)
   * Filters: market cap range, min ROCE, PAT > 0
   * Ranking: select 1-3 metrics to rank by
   * Position sizing: equal, market-cap, or metric-weighted
3. **Run backtest** → view results
4. **Export** results as CSV or Excel

\---

## Project Structure

```
backtesting-platform/
├── backend/
│   ├── app/
│   │   ├── models/          # ORM models
│   │   ├── schemas/         # Pydantic request/response
│   │   ├── routers/         # FastAPI routes
│   │   ├── engine/          # Backtest logic
│   │   ├── data/            # Data fetching
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings
│   │   └── database.py      # DB connection
│   ├── scripts/
│   │   └── ingest\_data.py   # CLI data ingestion
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── api/            # API client
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css       # Tailwind + custom styles
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── .env.example
└── README.md
```

\---

## Architecture

### Backend Flow

1. **Data Ingestion** → yfinance fetches prices + fundamentals → PostgreSQL
2. **Backtest Engine** → loads prices/fundamentals → applies filters → ranks → positions → calculates PnL
3. **FastAPI Router** → exposes `/api/backtest/run` endpoint
4. **Metrics** → computes CAGR, Sharpe, Sortino, Max Drawdown, etc.

### Frontend Flow

1. **Form** → user configures backtest params
2. **API Call** → POST to `/api/backtest/run`
3. **Results** → display equity curve, drawdown, metrics, portfolio logs
4. **Export** → save as CSV/Excel

\---

## Key Design Decisions

* **No Look-Ahead Bias:** Fundamentals for period T use data available before T
* **Idempotent Ingestion:** Can re-run `ingest\_data.py` safely (upserts on unique keys)
* **Modular Engine:** Filters, rankers, sizers, metrics are separate modules
* **Stateless API:** Each backtest request is independent
* **PostgreSQL Indexes:** `(stock\_id, date)` for fast price lookups

\---

## Common Issues

### Port Already in Use

```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9
# Or on Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### psycopg2 Install Fails

```bash
pip install psycopg2-binary
```

### Data Ingestion Slow

* First run downloads 10+ years of prices for 100+ stocks (\~10 minutes)
* Subsequent runs only fetch new data (fast)

### yfinance SSL Errors

```bash
pip install --upgrade certifi
```

\---

## Optional Enhancements

* \[ ] Prebuilt strategy templates
* \[ ] Docker containerization
* \[ ] Real-time strategy simulation
* \[ ] Machine learning model selection

\---

## Development

### Add New Ranking Metric

Edit `frontend/src/components/BacktestForm/index.jsx`:

```js
const METRICS = \['roe', 'roce', 'pe\_ratio', 'pb\_ratio', 'pat', 'market\_cap', 'NEW\_METRIC']
```

### Add New Filter

Edit `backend/app/engine/filters.py`:

```python
def apply\_filters(df: pd.DataFrame, cfg):
    # ... existing filters ...
    if cfg.your\_new\_filter:
        result = result\[result\["column"] > threshold]
```





\---

## License

MIT

\---

**Built for:** Qode Full Stack Developer Assignment  
**Author:** Hitesh Girish Shibag 
**Last Updated:** 2026/June

