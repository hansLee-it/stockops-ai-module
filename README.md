# StockOps AI Module

Demand forecasting microservice for StockOps inventory management system.

## Overview

This service provides AI-powered demand forecasting using Facebook Prophet.
It runs as a standalone FastAPI application and is consumed by the StockOps API Server.

## Features

- Single-product demand forecasting (`POST /predict`)
- Bulk forecasting (`POST /predict/bulk`)
- Model evaluation with MAE/RMSE/MAPE (`GET /evaluate/{product_id}`)
- Evaluation history (`GET /evaluate/history/{product_id}`)
- In-memory model caching with TTL

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run with Docker

```bash
docker build -t stockops-ai-module .
docker run -p 8000:8000 --env-file .env stockops-ai-module
```

## Verification

Run these commands from `stockops-ai-module/`:

```bash
python -m compileall .
python -m pytest
```

The pytest harness uses FastAPI `TestClient` with monkeypatched DB/model calls, so it does not require external secrets or a live database.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(required)* | PostgreSQL connection string |
| `AI_MODULE_API_KEY` | *(empty = dev mode)* | Shared secret for `X-API-Key` header auth |
| `SERVICE_HOST` | `0.0.0.0` | Uvicorn bind host |
| `SERVICE_PORT` | `8000` | Uvicorn bind port |
| `MODEL_CACHE_TTL_SECONDS` | `3600` | Prophet model cache TTL in seconds |
| `MODEL_CACHE_MAX_SIZE` | `10` | Max cached models before LRU eviction |
| `MIN_HISTORY_DAYS` | `14` | Minimum historical data days required |
| `MAPE_ALERT_THRESHOLD` | `30.0` | MAPE threshold for warning logs |
| `EVALUATION_TRAIN_RATIO` | `0.8` | Train/test split ratio for evaluation |
| `DB_POOL_MIN` | `2` | DB connection pool minimum connections |
| `DB_POOL_MAX` | `10` | DB connection pool maximum connections |
| `DB_CONNECT_TIMEOUT` | `10` | DB connection timeout in seconds |

## API Endpoints

| Method | Path | Auth required | Description |
|--------|------|---------------|-------------|
| GET | `/health` | No | Health check |
| POST | `/predict` | Yes | Single product forecast |
| POST | `/predict/bulk` | Yes | Bulk forecast (up to 50 products) |
| GET | `/evaluate/{product_id}` | Yes | Evaluate model accuracy |
| GET | `/evaluate/history/{product_id}` | Yes | Fetch evaluation history |

### POST /predict

Request:

```json
{
  "product_id": 1,
  "days": 7
}
```

Response (`200 OK`):

```json
{
  "product_id": 1,
  "days": 7,
  "forecast": [
    { "ds": "2026-06-01", "yhat": 10.25, "yhat_lower": 8.0, "yhat_upper": 12.5 }
  ]
}
```

Errors: `400` insufficient history, `422` invalid input, `500` model failure.

### POST /predict/bulk

Request:

```json
{
  "products": [
    { "product_id": 1, "days": 7 },
    { "product_id": 2, "days": 3 }
  ]
}
```

Response (`200 OK`): array of forecast objects (same shape as `/predict`).

Partial failure (`400`): returned when at least one product fails.

```json
{
  "detail": {
    "errors": ["product_id=2: Insufficient historical data for product 2."],
    "successful": 1
  }
}
```

### GET /evaluate/{product_id}

Response (`200 OK`):

```json
{
  "product_id": 1,
  "mae": 2.1234,
  "rmse": 3.4567,
  "mape": 12.5678,
  "model_version": "prophet"
}
```

### GET /evaluate/history/{product_id}

Query params: `limit` (1–100, default 20).

Response (`200 OK`):

```json
{
  "product_id": 1,
  "history": [
    { "id": 5, "mae": 2.1, "rmse": 3.4, "mape": 12.5, "evaluated_at": "...", "model_version": "prophet" }
  ]
}
```

### GET /health

Response (`200 OK`):

```json
{ "status": "ok" }
```

## Architecture

```
Request → FastAPI → forecasting.py → prophet_model.py
                           ↓
                     PostgreSQL (direct)
```

## License

Team Project - Educational Purpose
## Environment And Secrets

See [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) for local `.env`, GitHub Actions secrets, and deployment environment setup.

Never commit `.env`, real credentials, Terraform state, or AI-agent local configuration files.

## Data Storage

This service does not store AI chat conversations.

It reads product outbound history from the application database for forecasting and writes model evaluation results to `analytics.ai_model_evaluations`.
