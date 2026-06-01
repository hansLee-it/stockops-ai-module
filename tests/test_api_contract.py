import asyncio

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import main
from services import forecasting


API_KEY = "test-api-key"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(main, "AI_MODULE_API_KEY", API_KEY)
    return TestClient(main.app)


def auth_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


async def successful_forecast(product_id: int, days: int) -> dict[str, object]:
    return {
        "product_id": product_id,
        "days": days,
        "forecast": [
            {
                "ds": "2026-06-01",
                "yhat": 10.0,
                "yhat_lower": 8.0,
                "yhat_upper": 12.0,
            }
        ],
    }


def test_predict_rejects_missing_api_key(client: TestClient) -> None:
    response = client.post("/predict", json={"product_id": 1, "days": 1})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_predict_rejects_wrong_api_key(client: TestClient) -> None:
    response = client.post(
        "/predict",
        headers={"X-API-Key": "wrong-key"},
        json={"product_id": 1, "days": 1},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_predict_accepts_valid_api_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "forecast_async", successful_forecast)

    response = client.post(
        "/predict",
        headers=auth_headers(),
        json={"product_id": 1, "days": 1},
    )

    assert response.status_code == 200
    assert response.json()["product_id"] == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"product_id": 0, "days": 1},
        {"product_id": 1, "days": 0},
        {"product_id": 1, "days": 366},
    ],
)
def test_predict_request_validation_rejects_invalid_product_or_days(
    client: TestClient,
    payload: dict[str, int],
) -> None:
    response = client.post("/predict", headers=auth_headers(), json=payload)

    assert response.status_code == 422


def test_evaluate_rejects_invalid_product_id(client: TestClient) -> None:
    response = client.get("/evaluate/0", headers=auth_headers())

    assert response.status_code == 422


def test_evaluation_history_rejects_invalid_limit(client: TestClient) -> None:
    response = client.get("/evaluate/history/1?limit=0", headers=auth_headers())

    assert response.status_code == 400
    assert response.json()["detail"] == "limit must be between 1 and 100"


def test_predict_maps_data_shortage_to_bad_request(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def shortage_forecast(product_id: int, days: int) -> dict[str, object]:
        raise ValueError(
            f"Insufficient historical data for product {product_id}. Found 0 days, minimum required is 14."
        )

    monkeypatch.setattr(main, "forecast_async", shortage_forecast)

    response = client.post(
        "/predict",
        headers=auth_headers(),
        json={"product_id": 1, "days": 1},
    )

    assert response.status_code == 400
    assert "Insufficient historical data" in response.json()["detail"]


def test_forecast_async_raises_data_shortage_before_model_training(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forecasting._model_cache.clear()
    monkeypatch.setattr(forecasting, "MIN_HISTORY_DAYS", 14)
    monkeypatch.setattr(
        forecasting,
        "fetch_outbound_history",
        lambda product_id: pd.DataFrame(columns=["ds", "y"]),
    )

    with pytest.raises(ValueError, match="Insufficient historical data"):
        asyncio.run(forecasting.forecast_async(product_id=1, days=1))


def test_predict_maps_model_failure_to_server_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_forecast(product_id: int, days: int) -> dict[str, object]:
        raise RuntimeError("model prediction failed")

    monkeypatch.setattr(main, "forecast_async", failing_forecast)

    response = client.post(
        "/predict",
        headers=auth_headers(),
        json={"product_id": 1, "days": 1},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "model prediction failed"


def test_evaluation_history_maps_db_failure_to_server_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_history(product_id: int, limit: int) -> list[dict[str, object]]:
        raise RuntimeError("Database query failed")

    monkeypatch.setattr(main, "fetch_evaluation_history", failing_history)

    response = client.get("/evaluate/history/1", headers=auth_headers())

    assert response.status_code == 500
    assert response.json()["detail"] == "Database query failed"
