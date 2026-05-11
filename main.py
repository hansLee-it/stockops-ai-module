"""FastAPI application for demand forecasting with Facebook Prophet."""

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from services.forecasting import evaluate, fetch_evaluation_history, forecast

load_dotenv()

app = FastAPI(title="StockOps AI Forecasting Service", version="1.0.0")


class PredictRequest(BaseModel):
    """Request body for single-product demand forecasting."""

    product_id: int = Field(..., ge=1, description="Product identifier")
    days: int = Field(..., ge=1, le=365, description="Number of days to forecast")


class PredictResponse(BaseModel):
    """Response body for single-product demand forecasting."""

    product_id: int
    days: int
    forecast: list[dict[str, Any]]


class BulkPredictRequest(BaseModel):
    """Request body for bulk demand forecasting."""

    products: list[PredictRequest] = Field(..., min_length=1, max_length=50)


class EvaluateResponse(BaseModel):
    """Response body for forecast evaluation metrics."""

    product_id: int
    mae: float
    rmse: float
    mape: float
    model_version: str = "prophet"


class EvaluateHistoryResponse(BaseModel):
    """Response body for evaluation history."""

    product_id: int
    history: list[dict[str, Any]]


@app.get("/health", response_model=dict[str, str])
def health_check() -> dict[str, str]:
    """Return the health status of the service."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Generate a demand forecast for a single product."""
    try:
        result = forecast(request.product_id, request.days)
        return PredictResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@app.post("/predict/bulk", response_model=list[PredictResponse])
def predict_bulk(request: BulkPredictRequest) -> list[PredictResponse]:
    """Generate demand forecasts for multiple products in one request."""
    results: list[PredictResponse] = []
    errors: list[str] = []

    for item in request.products:
        try:
            result = forecast(item.product_id, item.days)
            results.append(PredictResponse(**result))
        except ValueError as exc:
            errors.append(f"product_id={item.product_id}: {exc}")
        except RuntimeError as exc:
            errors.append(f"product_id={item.product_id}: {exc}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors, "successful": len(results)},
        )

    return results


@app.get("/evaluate/{product_id}", response_model=EvaluateResponse)
def evaluate_model(product_id: int, model_version: str = "prophet") -> EvaluateResponse:
    """Evaluate forecast accuracy for a product using historical data."""
    try:
        result = evaluate(product_id, model_version)
        return EvaluateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@app.get("/evaluate/history/{product_id}", response_model=EvaluateHistoryResponse)
def evaluation_history(product_id: int, limit: int = 20) -> EvaluateHistoryResponse:
    """Fetch past evaluation results for a product."""
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 100",
        )
    try:
        history = fetch_evaluation_history(product_id, limit)
        return EvaluateHistoryResponse(product_id=product_id, history=history)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
