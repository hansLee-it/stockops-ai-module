"""Prophet model wrapper with in-memory caching and TTL."""

import time
from typing import Any

import pandas as pd
from prophet import Prophet


class ProphetModelCache:
    """In-memory cache for trained Prophet models with TTL expiration.

    Attributes:
        _cache: Dictionary mapping product_id to cached entry.
        _ttl_seconds: Time-to-live for cached models in seconds.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize the model cache.

        Args:
            ttl_seconds: TTL for cached models in seconds (default 1 hour).
        """
        self._cache: dict[int, dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds

    def get(self, product_id: int) -> Prophet | None:
        """Retrieve a cached Prophet model if it exists and is not expired.

        Args:
            product_id: The product identifier.

        Returns:
            The cached Prophet model, or None if missing or expired.
        """
        entry = self._cache.get(product_id)
        if entry is None:
            return None
        if time.time() - entry["timestamp"] > self._ttl_seconds:
            del self._cache[product_id]
            return None
        return entry["model"]

    def set(self, product_id: int, model: Prophet) -> None:
        """Store a trained Prophet model in the cache.

        Args:
            product_id: The product identifier.
            model: The trained Prophet model.
        """
        self._cache[product_id] = {
            "model": model,
            "timestamp": time.time(),
        }

    def clear(self) -> None:
        """Clear all cached models."""
        self._cache.clear()

    def invalidate(self, product_id: int) -> None:
        """Remove a specific product's model from the cache.

        Args:
            product_id: The product identifier.
        """
        self._cache.pop(product_id, None)


def create_prophet_model(yearly_seasonality: bool = True) -> Prophet:
    """Instantiate a new Prophet model with default settings.

    Args:
        yearly_seasonality: Enable yearly seasonality (default True).

    Returns:
        A new, untrained Prophet instance.
    """
    return Prophet(yearly_seasonality=yearly_seasonality)


def fit_prophet(model: Prophet, df: pd.DataFrame) -> Prophet:
    """Fit a Prophet model on historical daily data.

    The DataFrame must contain 'ds' (datetime) and 'y' (numeric) columns.

    Args:
        model: The Prophet model to train.
        df: Historical data with 'ds' and 'y' columns.

    Returns:
        The fitted Prophet model.
    """
    model.fit(df)
    return model


def predict_future(model: Prophet, days: int) -> pd.DataFrame:
    """Generate a forecast for the specified number of future days.

    Args:
        model: A trained Prophet model.
        days: Number of days to forecast.

    Returns:
        DataFrame with forecast columns including ds, yhat, yhat_lower, yhat_upper.
    """
    future = model.make_future_dataframe(periods=days)
    return model.predict(future)
