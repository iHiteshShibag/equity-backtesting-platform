# 📈 Equity Backtesting Platform

End-to-end backtesting platform for testing fundamental-based equity strategies on Indian stock markets (NIFTY 100 universe).

**Tech Stack:**

* Backend: Python 3.10+ + FastAPI + SQLAlchemy 2.0 + Alembic (migrations)
* Database: PostgreSQL 15 (via PgBouncer for connection pooling)
* Async workers: Celery + Redis — separate queues for backtests (`backtest`) and data ingestion (`ingestion`), plus `celery-beat` for scheduled jobs
* Frontend: React 18 + Vite + Tailwind CSS + Recharts, with route-level code-splitting (`React.lazy`)
* Data: yfinance (prices) + fundamentals via yfinance/Screener.in scraping
* Auth: JWT (short-lived access token + httpOnly refresh cookie), role-based access (admin/member)
* Rate limiting: SlowAPI (Redis-backed), limits scale with organization tier (free/pro/enterprise)
* Observability: Sentry (backend via `sentry-sdk`, frontend via `@sentry/react` — both no-op if no DSN is set) + structured JSON logging to stdout
* Testing/CI: pytest (backend unit + integration), ruff + mypy (lint/type-check), GitHub Actions (`.github/workflows/ci.yml`)

## Features

✅ **Backtest Engine**

* User-defined date ranges and rebalancing frequencies (monthly/quarterly/yearly)
* Portfolio sizing (top 20, 50, 100 stocks — any positive size)
* Filtering: market cap range, ROCE threshold, PAT > 0
* Ranking: single/multi-metric ranking with custom ordering (asc/desc per metric)
* Position sizing: equal-weight, market-cap-weight, metric-weight
* Optional commission (bps) and slippage (%) modeling per trade
* No look-ahead bias in fundamentals
* Compounding logic at each rebalance
* Runs asynchronously as a Celery job — the API queues the job and returns immediately (`202 Accepted`); the frontend polls for the result

✅ **Data Layer**

* 100+ Indian listed companies (Nifty 100)
* Historical price data (OHLCV) from 2015+
* Fundamental data: P&L, balance sheet, cash flow, and ratios (P/E, ROCE, ROE, PAT, etc.)
* Ingestion tracked via `IngestionRun` records — status, per-ticker success/failure counts, and a stale-run guard (a run stuck in "running" past 2 hours is marked failed so it doesn't block new runs, e.g. after a worker crash)
* Scheduled automatically on weekdays (post NSE-close) via `celery-beat`, or triggered manually from the Data Management screen / API

✅ **Analytics Dashboard**

* Equity curve visualization
* Drawdown analysis
* Benchmark CAGR comparison (Nifty 50)
* Alpha calculation vs benchmark
* Performance metrics: CAGR, Total Return, Sharpe, Sortino, Max Drawdown, Calmar, Win Rate, total transaction costs
* Rebalance logs with holdings and weights
* Top winners/losers stock list
* CSV/Excel export (client-side, via `xlsx` + `file-saver`)
* A pre-run "universe count" preview shows how many stocks currently match your filters before you run the full backtest

✅ **Saved Strategies & Alerts**

* Save any backtest configuration as a recurring strategy
* Daily Celery-beat job (`strategies.check_due`) re-runs due strategies and emails a rebalance summary to the owner
* Pause/resume or delete saved strategies from the dashboard

✅ **Point-in-Time Universe (Survivorship-Bias Mitigation)**

* `index_memberships` table restricts each rebalance to tickers that were actually NIFTY100 constituents on that date
* Seeded with known IPO/listing dates (see `backend/app/modules/market_data/index_membership_seed.py`) — best-effort, not a licensed index-history feed

✅ **Compliance & Multi-Tenancy Scaffolding**

* Users must accept a "not investment advice" disclaimer before running a backtest (`tos_accepted_at` gate)
* Organizations have a `tier` field (free/pro/enterprise) that drives tier-based API rate limits (5/30/120 requests per minute respectively) — scaffolding for a future SaaS pivot, no billing integration yet

✅ **User & Org Administration**

* Admin-only user management: list, create, update role/name/active status, delete (self-demotion/self-deletion is blocked)
* Admin-only organization tier management

---

## API Documentation

The backend exposes REST APIs through FastAPI.

Interactive Swagger documentation is available when the backend is running:

```text
http://127.0.0.1:8000/docs
```

Key endpoints (all `/api/*` routes except `/api/auth/login` and `/api/auth/refresh` require a valid access token):

| Method | Endpoint                      | Description                                                                 |
| ------ | ------------------------------ | ---------------------------------------------------------------------------- |
| POST   | /api/auth/login                | Log in, returns access token + sets an httpOnly refresh cookie              |
| POST   | /api/auth/refresh              | Exchange the refresh cookie for a new access token                          |
| POST   | /api/auth/logout               | Clear the refresh cookie                                                    |
| GET    | /api/auth/me                   | Current user profile                                                        |
| POST   | /api/auth/accept-tos           | Accept the disclaimer/ToS (required before running a backtest)             |
| POST   | /api/backtest/run              | Queue a backtest job with custom strategy parameters (requires ToS acceptance); returns `202` with a job id |
| GET    | /api/backtest/jobs/{id}        | Poll a queued backtest job for its status/result                            |
| GET    | /api/backtest/jobs             | List your most recent 50 backtest jobs                                      |
| GET    | /api/backtest/universe-count   | Preview how many stocks match a given filter set today                     |
| GET    | /api/backtest/health           | Backtest module health check                                                |
| GET    | /api/stocks/list                | List all stocks in the universe                                             |
| GET    | /api/stocks/{ticker}            | Get details for one stock                                                   |
| GET    | /api/market-data/status         | Row counts + latest/recent ingestion run history                            |
| POST   | /api/market-data/ingest         | Queue a manual data ingestion run (prices + fundamentals)                   |
| POST   | /api/strategies/                | Save a backtest config as a recurring, alertable strategy                   |
| GET    | /api/strategies/                | List your saved strategies                                                  |
| PATCH  | /api/strategies/{id}            | Pause/resume a saved strategy                                               |
| DELETE | /api/strategies/{id}            | Delete a saved strategy                                                     |
| GET    | /api/orgs/me                    | Your organization (name, tier)                                              |
| PATCH  | /api/orgs/me                    | Update org name/tier (admin only)                                           |
| GET    | /api/users                      | List users (admin only)                                                     |
| POST   | /api/users                      | Create a user (admin only)                                                  |
| PATCH  | /api/users/{id}                 | Update a user's role/name/active status (admin only)                        |
| DELETE | /api/users/{id}                 | Delete a user (admin only)                                                  |
| GET    | /docs                            | Interactive Swagger API documentation                                       |
| GET    | /openapi.json                   | OpenAPI specification                                                       |
| GET    | /health                          | Root-level liveness check                                                   |

A backtest run returns:

* Portfolio performance metrics (CAGR, Sharpe, Sortino, Max Drawdown, Calmar, Win Rate, total costs)
* Equity curve time series
* Drawdown data
* Rebalance logs
* Benchmark comparison metrics
* Top winners and losers
* Data quality notes (e.g. gaps in fundamentals)

---

## Prerequisites

* **Docker + Docker Compose** → [docker.com](https://docker.com) (recommended path below)
* Or, for a manual setup: **Python 3.10+**, **Node.js 18+**, **PostgreSQL 15+**, **Redis 7**

---

## Installation & Setup

### Option A: Docker Compose (recommended)

```bash
# From the repo root
cp .env.example .env   # edit if you want non-default secrets/credentials
docker compose up --build
```

This starts everything: Postgres, PgBouncer, Redis, the FastAPI backend (with migrations run automatically via the `migrate` service and an admin user seeded via `seed-admin`), separate Celery workers for the `backtest` and `ingestion` queues, `celery-beat` for scheduled ingestion + daily strategy-alert checks, and the Vite frontend.

* Frontend: `http://localhost:5174` (container's Vite dev server on 5173 is mapped to host port 5174 in `docker-compose.yml`)
* Backend / Swagger docs: `http://localhost:8000/docs`

To (re-)apply migrations manually, e.g. after pulling new ones:

```bash
docker compose exec backend alembic upgrade head
```

To trigger data ingestion (first run takes 5–10 minutes for 100+ tickers), either use the Data Management screen in the UI, call `POST /api/market-data/ingest`, or run the CLI script directly:

```bash
docker compose exec backend python scripts/ingest_data.py
```

Scale backtest workers horizontally if needed (PgBouncer keeps total Postgres connections bounded):

```bash
docker compose up --scale celery-worker-backtest=3
```

### Option B: Manual setup

```bash
# --- Database ---
createdb backtesting_db

# --- Backend ---
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt   # or requirements/prod.txt for a production install

cp .env.example .env
# Edit .env: DATABASE_URL, REDIS_URL/CELERY_BROKER_URL, SECRET_KEY, etc.

alembic upgrade head
python scripts/seed_admin.py       # creates the bootstrap admin (see ADMIN_EMAIL/ADMIN_PASSWORD in .env)
python scripts/ingest_data.py      # first run takes 5-10 minutes

uvicorn app.main:app --reload      # runs at http://localhost:8000
# In separate terminals:
celery -A app.worker.celery_app worker --loglevel=info --queues=backtest
celery -A app.worker.celery_app worker --loglevel=info --queues=ingestion
celery -A app.worker.celery_app beat --loglevel=info

# --- Frontend ---
cd frontend
npm install
cp .env.example .env   # VITE_API_URL, optionally VITE_SENTRY_DSN
npm run dev                          # runs at http://localhost:5173
```

### Option C: Production deployment

`docker-compose.prod.yml` is an overlay on top of the base file (not a replacement) — `db`/`redis`/`pgbouncer`/`migrate`/`seed-admin` don't need anything different in prod, so it only overrides what does:

```bash
cp .env.example .env    # set real SECRET_KEY/ADMIN_PASSWORD, ENVIRONMENT=production, CORS_ORIGINS
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

What changes vs. the dev compose file:

* **`backend`/`celery-*`** build from `backend/Dockerfile.prod` (installs `requirements/prod.txt`, no dev tooling) and run under **gunicorn** with `uvicorn.workers.UvicornWorker` instead of `uvicorn --reload`. No source bind-mount — the image is the deployed code, not a live view into the host checkout. `GUNICORN_WORKERS` (default 4) controls worker count.
* **`backend`** no longer publishes port 8000 to the host — only `frontend` is public.
* **`frontend`** builds from `frontend/Dockerfile.prod`: a static Vite build served by **nginx** (`frontend/nginx.conf`), which also reverse-proxies `/api/`, `/docs`, `/redoc`, and `/openapi.json` to the `backend` service so the browser only ever talks to one origin. `HTTP_PORT` (default 80) controls the published host port. `/metrics` (Prometheus) is blocked at this edge — it's meant for an internal scraper, not public access.
* All services get `restart: unless-stopped`.

**TLS**: the nginx config ships with a plain `listen 80` server block. For a real domain, get a cert (e.g. `certbot certonly --standalone -d yourdomain.com`), mount `/etc/letsencrypt` into the `frontend` container, and add a `listen 443 ssl` server block to `frontend/nginx.conf` pointing at the mounted cert/key — then redirect port 80 to 443.

### Environment variables

Three separate `.env.example` files document configuration at different levels:

* **Root `.env.example`** — Docker Compose–level: Postgres credentials, host port mappings, `CORS_ORIGINS`, `SECRET_KEY`, bootstrap admin credentials, and optional Sentry DSNs (backend and frontend use *separate* DSNs/projects).
* **`backend/.env.example`** — FastAPI service config for a manual (non-Docker) run: `DATABASE_URL`, `CORS_ORIGINS`, JWT settings (`SECRET_KEY`, `JWT_ALGORITHM`, token expiry), admin bootstrap credentials, `ENVIRONMENT`/`DEBUG`.
* **`frontend/.env.example`** — just `VITE_API_URL` (backend base URL).

Other backend settings (see `backend/app/core/config.py` for full defaults): `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` / `DB_POOL_RECYCLE_SECONDS` (SQLAlchemy pool tuning), `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`, `LOG_LEVEL`, `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `EMAIL_FROM` (rebalance-alert emails — left blank in dev, which just logs a warning and skips sending instead of failing).

---

## Usage

1. **Open** `http://localhost:5173` (manual setup) or `http://localhost:5174` (Docker) in your browser and log in with the seeded admin credentials
2. **Accept the disclaimer** (one-time) — backtests are blocked until you do
3. **Populate data** — if the database is empty, the dashboard shows a prompt to trigger ingestion (Data Management screen or `POST /api/market-data/ingest`)
4. **Configure backtest parameters:**

   * Date range (e.g., 2018-2024)
   * Rebalance frequency (monthly/quarterly/yearly)
   * Portfolio size (top 20, 50, 100 stocks, or any custom size)
   * Filters: market cap range, min ROCE, PAT > 0 — a live "universe count" shows how many stocks currently match
   * Ranking: select 1-3 metrics to rank by, each ascending or descending
   * Position sizing: equal, market-cap, or metric-weighted
   * Optional commission (bps) and slippage (%) assumptions
5. **Run backtest** → the job queues, the frontend polls `/api/backtest/jobs/{id}`, then results render
6. **Export** results as CSV or Excel, or **Save as Strategy** to get emailed when it's next due for rebalance
7. **Admins** can additionally manage users/roles and organization tier from the sidebar

---

## Project Structure

```
backtesting-platform/
├── backend/
│   ├── app/
│   │   ├── core/             # Settings (config.py), logging/Sentry setup (observability.py), rate limiting (rate_limit.py), email (email.py), Redis response caching (cache.py), defensive response headers (security_headers.py)
│   │   ├── db/                # Base declarative class + session/engine
│   │   ├── modules/
│   │   │   ├── auth/          # JWT auth, User model, ToS-acceptance gate
│   │   │   ├── users/         # Admin user management
│   │   │   ├── orgs/          # Organization/tier scaffolding (multi-tenancy)
│   │   │   ├── stocks/        # Stock/DailyPrice/Fundamental models + router
│   │   │   ├── backtest/      # Backtest router, schemas, async job model, engine/
│   │   │   ├── strategies/    # Saved strategies + rebalance-alert Celery task
│   │   │   └── market_data/   # yfinance fetchers, NIFTY100 universe, point-in-time index membership, ingestion tasks/router
│   │   ├── worker.py           # Celery app + beat schedule
│   │   └── main.py            # FastAPI app, CORS, rate-limit + exception handlers
│   ├── alembic/                # DB migrations (11 revisions)
│   ├── scripts/
│   │   ├── ingest_data.py     # CLI data ingestion
│   │   └── seed_admin.py      # Creates the bootstrap admin user
│   ├── tests/
│   │   ├── unit/               # Engine (filters/rankers/sizers/metrics), Celery tasks, fundamentals/index-membership logic
│   │   └── integration/        # Router-level tests per module (auth, backtest, market_data, orgs, stocks, strategies, users, config)
│   ├── requirements/
│   │   ├── base.txt            # Runtime deps (FastAPI, SQLAlchemy, Celery, yfinance, etc.)
│   │   ├── dev.txt             # + ruff, mypy, black, pytest, httpx, ipdb
│   │   └── prod.txt            # + gunicorn
│   ├── pytest.ini              # pytest-cov wired in, 80% coverage floor (--cov-fail-under)
│   ├── Dockerfile               # dev image (uvicorn --reload via docker-compose.yml's command)
│   ├── Dockerfile.prod          # prod image: gunicorn + uvicorn.workers.UvicornWorker
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── backtest/       # Backtest form, charts (EquityCurve/DrawdownChart), metrics panel, portfolio log, export button, api.js
│   │   │   ├── strategies/     # Saved strategies list + save-as-strategy api.js
│   │   │   ├── stocks/         # Stock list/detail api.js
│   │   │   ├── dataManagement/ # Ingestion trigger + status view
│   │   │   ├── orgs/           # Organization card (tier display/edit)
│   │   │   ├── userAdmin/      # User admin table (admin only)
│   │   │   └── universe/       # Reserved for future universe-browsing UI
│   │   ├── components/         # Generic, domain-agnostic UI building blocks (DisclaimerGate, LoginScreen, Sidebar, EmptyState, icons)
│   │   ├── context/             # AuthContext (auth state/provider)
│   │   ├── api/                 # Shared axios client (client.js) + auth token store (authStore.js)
│   │   ├── App.jsx              # View router (dashboard/strategies/data/users), lazy-loaded routes
│   │   ├── main.jsx
│   │   └── index.css           # Tailwind + custom styles
│   ├── index.html
│   ├── vite.config.js
│   ├── vitest.config.js        # Vitest + jsdom, extends vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   ├── Dockerfile               # dev image (Vite dev server)
│   ├── Dockerfile.prod          # prod image: static build served by nginx
│   ├── nginx.conf                # prod nginx: SPA fallback, /api reverse proxy, security headers
│   └── .env.example
├── scripts/
│   ├── bootstrap.py            # Repo-level bootstrap helper
│   └── check_paths.py          # Repo-level path/sanity checker
├── docker-compose.yml
├── docker-compose.prod.yml     # Production overlay (gunicorn, nginx, no dev bind-mounts) -- see "Production deployment"
└── .github/workflows/ci.yml    # Backend (ruff, mypy, pytest w/ Redis) + frontend (lint, vitest, build) + docker-build (backend/frontend prod images)
```

---

## Architecture

### Backend Flow

1. **Data Ingestion** → yfinance/Screener.in fetches prices + fundamentals → PostgreSQL, tracked via `IngestionRun` rows; runs on the `ingestion` Celery queue, scheduled weekdays post NSE-close or triggered manually
2. **Backtest Request** → `POST /api/backtest/run` creates a `BacktestJob` row (status `pending`) and enqueues it on the `backtest` Celery queue; the API responds immediately with `202` and a job id
3. **Backtest Engine** (Celery task) → loads prices/fundamentals → restricts to point-in-time NIFTY100 members → applies filters → ranks → sizes positions → calculates PnL (with optional commission/slippage) → writes the result back onto the job row
4. **Frontend polls** `GET /api/backtest/jobs/{id}` until the job's status is `success`/`failure`
5. **Metrics** → computes CAGR, Sharpe, Sortino, Max Drawdown, Calmar, Win Rate
6. **Saved Strategies** → `celery-beat` runs `strategies.check_due` daily, re-running due strategies and emailing owners
7. **Rate limiting** → SlowAPI enforces per-organization-tier limits (Redis-backed, so shared across replicas) on top of auth/ToS gating
8. **Caching** → `app/core/cache.py` caches a handful of read-heavy, interactive endpoints (`/api/backtest/universe-count`, `/api/stocks/list`) in Redis for a few minutes; reads/writes fail open on any Redis error, so a cache blip degrades to "slower," never "broken"
9. **Circuit breaker** → both ingestion fetchers (`fetcher.py`, `fundamentals_screener.py`) abort early after ~15 consecutive per-ticker failures instead of grinding through the rest of the universe against a source that's blocking/down; an aborted or fully-failed run pages Sentry
10. **Observability** → structured JSON logs to stdout always; Sentry error tracking is enabled only when `SENTRY_DSN` is set (backend/Celery) — no-ops otherwise; `/metrics` exposes Prometheus request-count/latency histograms (blocked from public access at the prod nginx edge — see `frontend/nginx.conf`)
11. **Security headers** → every response gets HSTS, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, a strict CSP (`default-src 'none'`, relaxed only for `/docs`/`/redoc`), etc. — see `app/core/security_headers.py`

### Frontend Flow

1. **Form** → user configures backtest params, sees a live universe-count preview
2. **API Call** → `POST /api/backtest/run`, then polls `/api/backtest/jobs/{id}`
3. **Results** → display equity curve, drawdown, metrics, rebalance/portfolio logs, winners/losers
4. **Export** → save as CSV/Excel client-side, or save the config as a recurring alertable Strategy
5. **Admin views** (lazy-loaded, admin-only for Users) → Data Management (ingestion status/trigger), Saved Strategies, User Admin, Organization tier

---

## Key Design Decisions

* **No Look-Ahead Bias:** Fundamentals for period T use data available before T
* **Point-in-Time Universe:** Each rebalance is restricted to tickers that were actually NIFTY100 members on that date (`index_memberships`), avoiding survivorship bias from applying today's constituent list to past dates
* **Idempotent Ingestion:** Can re-run `ingest_data.py` safely (upserts on unique keys); stale "running" ingestion runs (past a 2-hour threshold) are auto-marked failed so a crashed worker never blocks new runs indefinitely
* **Async Backtests:** Backtests run as Celery jobs rather than blocking the request — keeps the API responsive and lets backtest/ingestion workloads scale independently on separate queues
* **Modular Engine:** Filters, rankers, sizers, metrics are separate modules (`backend/app/modules/backtest/engine/`)
* **Tier-Based Rate Limiting:** Per-organization limits (free/pro/enterprise) enforced via Redis-backed SlowAPI, resolved through a contextvar set during auth so dynamic-limit lookups don't need direct Request access
* **PostgreSQL Indexes:** `(stock_id, date)` for fast price lookups
* **Connection Pooling:** PgBouncer sits in front of Postgres so multiple backend/worker replicas don't exhaust Postgres's own connection ceiling; migrations/seeding bypass it and talk to Postgres directly
* **Not Investment Advice:** Users must accept a disclaimer before running backtests; results are hypothetical, not a recommendation

---

## Testing

```bash
cd backend
source venv/bin/activate
pytest -q                 # full suite (unit + integration); pytest.ini wires in coverage automatically
pytest tests/unit -q      # engine/task logic only
pytest tests/integration -q  # router-level tests (need Redis reachable for rate-limit + cache tests)
```

`pytest.ini` always runs with `--cov=app --cov-report=term-missing --cov-fail-under=80` — the suite fails if coverage drops below 80% (currently ~88%), separately from whether the tests themselves pass.

```bash
cd frontend
npm test              # vitest run — lib/format, lib/errors, useAsyncList hook, LoginScreen component
npm run test:watch    # same, in watch mode
npm run test:coverage # with a coverage report (no enforced floor yet — only a handful of modules have tests so far)
```

CI (`.github/workflows/ci.yml`) runs on every push to `main` and every PR:

* **Backend job:** spins up a Redis service container, installs `requirements/dev.txt`, runs `ruff check app`, `mypy app` (non-blocking — see the job's comments for why), and `pytest -q` (coverage-gated per above)
* **Frontend job:** `npm ci`, `npm run lint`, `npm test`, `npm run build`
* **docker-build job:** builds `backend/Dockerfile.prod` and `frontend/Dockerfile.prod` (build-only — no registry configured yet, so nothing is pushed) to catch Dockerfile/build-context breakage before it reaches a deploy

---

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

* First run downloads 10+ years of prices for 100+ stocks (~10 minutes)
* Subsequent runs only fetch new data (fast)

### yfinance SSL Errors

```bash
pip install --upgrade certifi
```

### "Ingestion is already running" on manual trigger

A previous ingestion run is still marked `running`. If it's genuinely stuck (e.g. the worker crashed), it will auto-clear once it's older than 2 hours; otherwise check `GET /api/market-data/status` for the latest run's state.

---

## Optional Enhancements

* [ ] Prebuilt strategy templates
* [x] Docker containerization (dev **and** production — see `docker-compose.prod.yml`)
* [x] Saved strategies with rebalance-due email alerts
* [x] Async backtest execution via job queue
* [x] Sentry error tracking (backend + frontend), including on ingestion circuit-breaker trips/full failures
* [x] Prometheus metrics (`/metrics`) + Redis-backed response caching for hot read endpoints
* [x] Frontend test suite (Vitest + React Testing Library) and backend coverage enforcement (80% floor)
* [ ] Real-time strategy simulation
* [ ] Machine learning model selection
* [ ] Licensed market-data vendor (replace yfinance/Screener.in scraping — the circuit breaker in `fetcher.py`/`fundamentals_screener.py` makes a source outage fail fast and page Sentry rather than silently degrade, but doesn't remove the underlying fragility of an unlicensed scrape)
* [ ] Full multi-tenant billing (Stripe/Razorpay) on top of the org/tier scaffolding
* [ ] OpenTelemetry distributed tracing (Sentry APM + `/metrics` cover errors/request-level metrics today; no tracing backend is configured yet)
* [ ] CD pipeline — CI builds and discards Docker images today; wiring up a registry push + deploy step needs a chosen registry/host first

---

## Development

### Add New Ranking Metric

Edit `frontend/src/features/backtest/BacktestForm/index.jsx`:

```js
const METRICS = ['roe', 'roce', 'pe_ratio', 'pb_ratio', 'pat', 'market_cap', 'NEW_METRIC']
```

### Add New Filter

Edit `backend/app/modules/backtest/engine/filters.py`:

```python
def apply_filters(df: pd.DataFrame, cfg):
    # ... existing filters ...
    if cfg.your_new_filter:
        result = result[result["column"] > threshold]
```

Remember to also add the corresponding field to `BacktestRequest` in `backend/app/modules/backtest/schemas.py`.

### Add a DB migration

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

<img width="475" height="396" alt="01" src="https://github.com/user-attachments/assets/2a304ca6-74ca-4d92-a731-c1879b847367" />
<img width="316" height="146" alt="02" src="https://github.com/user-attachments/assets/3d66898c-d96d-4d23-95ce-f19ba3ac5cfc" />
<img width="476" height="425" alt="03" src="https://github.com/user-attachments/assets/55c141dd-93d5-4455-a7d4-4e6605466679" />
<img width="477" height="237" alt="04" src="https://github.com/user-attachments/assets/9fc6f459-29b9-4767-a485-b27957d39ddc" />

---

## License

MIT

---

**Author:** Hitesh Girish Shibag
**Last Updated:** 2026/July
