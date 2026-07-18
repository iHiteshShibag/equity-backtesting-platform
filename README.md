# 📈 Equity Backtesting Platform

<div align="center">

### Production-Grade Quantitative Equity Research & Backtesting Platform

Design, test, and analyze factor-based investment strategies on the Indian stock market using historical price and fundamental data.

**Live Demo:** https://equity-backtesting-platform.vercel.app/

---

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)
![Railway](https://img.shields.io/badge/Backend-Railway-0B0D0E)

</div>

---

> **Complete workflow:** Login → Configure Strategy → Run Backtest → View Analytics → Export Results
>
> ### Demo Credentials

| Field | Value |
|-------|-------|
| Email | demo@example.com |
| Password | demo1234 |

---

## 🚀 Overview

Equity Backtesting Platform is a production-ready full-stack application built for quantitative equity research on the Indian stock market.

Instead of being a simple CRUD dashboard, the platform simulates historical investment strategies using fundamental filters, ranking models, portfolio construction logic, and benchmark comparison while leveraging asynchronous background processing for scalability.

It demonstrates modern software engineering practices including production deployment, authentication, background workers, Dockerized infrastructure, CI/CD, monitoring, and cloud hosting.

---

## ✨ Highlights

- Production deployment (Vercel + Railway)
- FastAPI REST API
- React + Vite frontend
- PostgreSQL database
- Redis caching & broker
- Celery asynchronous workers
- JWT Authentication
- Role-Based Access Control
- Dockerized services
- CI/CD with GitHub Actions
- Interactive portfolio analytics
- CSV & Excel export
- Strategy scheduling & alerts

---

## 🏗️ Architecture

```mermaid
flowchart LR

A[React Frontend]
B[FastAPI API]
C[Redis]
D[Celery Workers]
E[(PostgreSQL)]
F[yFinance]

A --> B
B --> E
B --> C
C --> D
D --> E
D --> F
```

------------------------------------------------------------------------

# 🔄 Backtesting Workflow

``` mermaid
sequenceDiagram
User->>Frontend: Configure Strategy
Frontend->>API: Submit Request
API->>Redis: Queue Job
Redis->>Celery: Execute
Celery->>Market: Fetch Data
Celery->>DB: Store Results
Frontend->>API: Poll Status
API-->>Frontend: Completed Analytics
```

------------------------------------------------------------------------

## ✨ Features

### Quantitative Research

- Multi-factor ranking
- Fundamental screening
- Portfolio sizing
- Historical simulations
- Benchmark comparison
- Rebalancing engine
- Commission modelling
- Slippage modelling

### Analytics

- CAGR
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio
- Maximum Drawdown
- Alpha
- Equity Curve
- Portfolio Logs
- Winners & Losers
- Export to CSV & Excel

### Platform Features

- JWT Authentication
- Role-based access
- Scheduled strategies
- Email notifications
- Background processing
- REST APIs
- Swagger documentation
- Health checks

---

## ⚙️ Tech Stack

### Frontend

- React 18
- Vite
- Tailwind CSS
- Recharts
- Axios

### Backend

- FastAPI
- SQLAlchemy
- Alembic
- Celery
- Redis
- PostgreSQL

### DevOps

- Docker
- GitHub Actions
- Railway
- Vercel
- Gunicorn
- Nginx

---

## 📂 Project Structure

```text
backend/
frontend/
docker-compose.yml
docker-compose.prod.yml
.github/
scripts/
```

---

## 🚀 Local Setup

```bash
git clone <repo-url>

cd equity-backtesting-platform

cp .env.example .env

docker compose up --build
```

Frontend

```
http://localhost:5174
```

Backend

```
http://localhost:8000
```

Swagger

```
http://localhost:8000/docs
```

---

## 🐳 Docker

```bash
docker compose up --build
```

Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## ☁️ Production Deployment

| Service | Platform |
|---------|----------|
| Frontend | Vercel |
| Backend | Railway |
| Database | PostgreSQL |
| Queue | Redis |
| Workers | Celery |

---

## 📊 API Documentation

Swagger UI

```
/docs
```

OpenAPI

```
/openapi.json
```

---

## 🧪 Testing

Backend

```bash
pytest
```

Frontend

```bash
npm test
```

---

## 📈 Performance

- Async background execution
- Redis caching
- Connection pooling
- Docker containers
- Production-ready deployment
- Structured logging
- Horizontal worker scaling

---

# 📸 Screenshots

## Dashboard

<img width="959" height="510" alt="Screenshot 2026-07-18 171208" src="https://github.com/user-attachments/assets/007704a6-375e-4d0d-abdc-6fdff5805d43" />

---

## Running a Backtest

<img width="959" height="510" alt="Screenshot 2026-07-18 171229" src="https://github.com/user-attachments/assets/07ef14f1-083b-46eb-9a55-2f20a005ab09" />

---

## Saved Strategies

<img width="959" height="511" alt="Screenshot 2026-07-18 171252" src="https://github.com/user-attachments/assets/df30fc34-d2ad-4868-bce1-10e596d07da1" />

---

## Data Management

<img width="959" height="511" alt="Screenshot 2026-07-18 171304" src="https://github.com/user-attachments/assets/45cc5221-35a3-43bf-a92b-6c304833d5f6" />

---

## Your Profile

<img width="959" height="509" alt="Screenshot 2026-07-18 171350" src="https://github.com/user-attachments/assets/5c88b056-9c94-4569-9e3c-dfef87e679a8" />

---

## User Admin

<img width="959" height="512" alt="Screenshot 2026-07-18 171316" src="https://github.com/user-attachments/assets/77dafcc7-eaec-4ea3-b261-76d6b435edb2" />

---

## 🗺️ Roadmap

- ✅ Async Backtesting
- ✅ Portfolio Analytics
- ✅ Docker Deployment
- ✅ Production Hosting
- ✅ Strategy Alerts
- ⏳ Machine Learning Models
- ⏳ Live Market Data
- ⏳ Portfolio Optimizer
- ⏳ Broker Integration

---

## 🤝 Contributing

Contributions, feature requests, and bug reports are welcome.

Fork → Branch → Commit → Pull Request

---

## 📜 License

MIT

---

## 👨‍💻 Author

**Hitesh Girish Shibag**

If you found this project useful, consider giving it a ⭐ on GitHub.
