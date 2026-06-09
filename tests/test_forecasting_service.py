"""Unit tests for forecasting service helpers and forecast_async."""

import asyncio

import pandas as pd
import pytest

from services import forecasting


class FakeModel:
    def predict(self, future: pd.DataFrame) -> pd.DataFrame:
        output = future.copy()
        output["yhat"] = 10.25
        output["yhat_lower"] = 8.0
        output["yhat_upper"] = 12.5
        return output

    def make_future_dataframe(self, periods: int) -> pd.DataFrame:
        return pd.DataFrame({"ds": pd.date_range("2026-06-01", periods=periods, freq="D")})


def test_fill_missing_dates_inserts_zero_demand_days() -> None:
    df = pd.DataFrame({
        "ds": pd.to_datetime(["2026-06-01", "2026-06-03"]),
        "y": [5.0, 7.0],
    })

    result = forecasting._fill_missing_dates(df)

    assert list(result["y"]) == [5.0, 0.0, 7.0]


def test_forecast_async_returns_rounded_forecast(monkeypatch: pytest.MonkeyPatch) -> None:
    forecasting._model_cache.clear()

    async def fake_train(product_id: int) -> FakeModel:
        return FakeModel()

    monkeypatch.setattr(forecasting, "train_or_load_model_async", fake_train)

    result = asyncio.run(forecasting.forecast_async(product_id=1, days=2))

    assert result["product_id"] == 1
    assert result["days"] == 2
    assert result["forecast"][0]["yhat"] == 10.25
