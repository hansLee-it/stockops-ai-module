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
| `SERVICE_HOST` | `0.0.0.0` | Uvicorn bind host |
| `SERVICE_PORT` | `8000` | Uvicorn bind port |
| `MODEL_CACHE_TTL_SECONDS` | `3600` | Prophet model cache TTL |
| `MIN_HISTORY_DAYS` | `14` | Minimum historical data days required |
| `MAPE_ALERT_THRESHOLD` | `30.0` | MAPE threshold for warning logs |
| `EVALUATION_TRAIN_RATIO` | `0.8` | Train/test split ratio for evaluation |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/predict` | Single product forecast |
| POST | `/predict/bulk` | Bulk forecast |
| GET | `/evaluate/{product_id}` | Evaluate model accuracy |
| GET | `/evaluate/history/{product_id}` | Fetch evaluation history |

## Architecture

```
Request → FastAPI → forecasting.py → prophet_model.py
                           ↓
                     PostgreSQL (direct)
```

## License

Team Project - Educational Purpose
