"""Forecasting service: data fetching, model training, evaluation."""

import logging
import os
from typing import Any

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

from models.prophet_model import (
    ProphetModelCache,
    create_prophet_model,
    fit_prophet,
    predict_future,
)

logger = logging.getLogger(__name__)

MIN_HISTORY_DAYS = int(os.environ.get("MIN_HISTORY_DAYS", "14"))
MODEL_CACHE_TTL_SECONDS = int(os.environ.get("MODEL_CACHE_TTL_SECONDS", "3600"))
MAPE_ALERT_THRESHOLD = float(os.environ.get("MAPE_ALERT_THRESHOLD", "30.0"))
EVALUATION_TRAIN_RATIO = float(os.environ.get("EVALUATION_TRAIN_RATIO", "0.8"))

_model_cache = ProphetModelCache(ttl_seconds=MODEL_CACHE_TTL_SECONDS)


def _get_db_connection() -> psycopg2.extensions.connection:
    """Open a connection to the PostgreSQL database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    try:
        return psycopg2.connect(db_url)
    except psycopg2.Error as exc:
        raise RuntimeError(f"Failed to connect to database: {exc}") from exc


def fetch_outbound_history(product_id: int) -> pd.DataFrame:
    """Fetch daily aggregated outbound quantities for a product."""
    query = """
        SELECT o.outbound_date AS ds, SUM(oi.quantity) AS y
        FROM outbounds o
        JOIN outbound_items oi ON o.id = oi.outbound_id
        WHERE oi.product_id = %s
          AND o.status = 'CONFIRMED'
        GROUP BY o.outbound_date
        ORDER BY o.outbound_date
    """
    conn = _get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (product_id,))
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        raise RuntimeError(f"Database query failed: {exc}") from exc
    finally:
        conn.close()

    if not rows:
        return pd.DataFrame(columns=["ds", "y"])

    df = pd.DataFrame(rows)
    df["ds"] = pd.to_datetime(df["ds"])
    df["y"] = df["y"].astype(float)
    return df


def _fill_missing_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing dates with zero quantity to create a complete daily series."""
    if df.empty:
        return df.copy()
    full_range = pd.date_range(start=df["ds"].min(), end=df["ds"].max(), freq="D")
    df = df.set_index("ds").reindex(full_range, fill_value=0.0).reset_index()
    df = df.rename(columns={"index": "ds"})
    return df


def train_or_load_model(product_id: int) -> Any:
    """Return a trained Prophet model for the given product, using cache if available."""
    cached = _model_cache.get(product_id)
    if cached is not None:
        return cached

    df = fetch_outbound_history(product_id)
    df = _fill_missing_dates(df)

    if len(df) < MIN_HISTORY_DAYS:
        raise ValueError(
            f"Insufficient historical data for product {product_id}. "
            f"Found {len(df)} days, minimum required is {MIN_HISTORY_DAYS}."
        )

    model = create_prophet_model(yearly_seasonality=True)
    model = fit_prophet(model, df)
    _model_cache.set(product_id, model)
    return model


def forecast(product_id: int, days: int) -> dict[str, Any]:
    """Generate a demand forecast for a product."""
    if days <= 0:
        raise ValueError("days must be a positive integer")

    model = train_or_load_model(product_id)
    forecast_df = predict_future(model, days)

    future_df = forecast_df.tail(days)
    records = []
    for _, row in future_df.iterrows():
        records.append({
            "ds": row["ds"].strftime("%Y-%m-%d"),
            "yhat": round(float(row["yhat"]), 2),
            "yhat_lower": round(float(row["yhat_lower"]), 2),
            "yhat_upper": round(float(row["yhat_upper"]), 2),
        })

    return {
        "product_id": product_id,
        "days": days,
        "forecast": records,
    }


def _store_evaluation(product_id: int, mae: float, rmse: float, mape: float, model_version: str) -> None:
    """Persist evaluation metrics into the analytics.ai_model_evaluations table."""
    query = """
        INSERT INTO analytics.ai_model_evaluations (product_id, mae, rmse, mape, model_version)
        VALUES (%s, %s, %s, %s, %s)
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, (product_id, mae, rmse, mape, model_version))
            conn.commit()
    except psycopg2.Error as exc:
        raise RuntimeError(f"Failed to store evaluation result: {exc}") from exc
    finally:
        conn.close()


def fetch_evaluation_history(product_id: int, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch past evaluation results for a product, ordered by most recent first."""
    query = """
        SELECT id, mae, rmse, mape, evaluated_at, model_version
        FROM analytics.ai_model_evaluations
        WHERE product_id = %s
        ORDER BY evaluated_at DESC
        LIMIT %s
    """
    conn = _get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (product_id, limit))
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        raise RuntimeError(f"Database query failed: {exc}") from exc
    finally:
        conn.close()
    return [dict(row) for row in rows]


def evaluate(product_id: int, model_version: str = "prophet") -> dict[str, Any]:
    """Evaluate forecast accuracy using cross-validation on historical data."""
    df = fetch_outbound_history(product_id)
    df = _fill_missing_dates(df)

    if len(df) < MIN_HISTORY_DAYS * 2:
        raise ValueError(
            f"Insufficient data for evaluation for product {product_id}. "
            f"Found {len(df)} days, minimum required is {MIN_HISTORY_DAYS * 2}."
        )

    split_idx = int(len(df) * EVALUATION_TRAIN_RATIO)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    model = create_prophet_model(yearly_seasonality=True)
    model.fit(train_df)

    future = model.make_future_dataframe(periods=len(test_df))
    forecast_df = model.predict(future)
    pred_df = forecast_df.tail(len(test_df)).reset_index(drop=True)
    actuals = test_df["y"].values
    predictions = pred_df["yhat"].values

    mae = float(np.mean(np.abs(actuals - predictions)))
    rmse = float(np.sqrt(np.mean((actuals - predictions) ** 2)))
    mape = float(np.mean(np.abs((actuals - predictions) / np.where(actuals == 0, 1, actuals))) * 100)

    result = {
        "product_id": product_id,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 4),
        "model_version": model_version,
    }

    _store_evaluation(product_id, result["mae"], result["rmse"], result["mape"], model_version)

    if mape > MAPE_ALERT_THRESHOLD:
        logger.warning(
            "AI model evaluation alert: product_id=%s MAPE=%.2f%% exceeds %.1f%% threshold (model=%s)",
            product_id, mape, MAPE_ALERT_THRESHOLD, model_version,
        )

    return result
