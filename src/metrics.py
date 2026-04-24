"""Financial performance metrics for daily stock return data."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


def prepare_stock_data(data: pd.DataFrame) -> pd.DataFrame:
    """Clean daily price/return data and add cumulative performance fields."""
    if data.empty:
        raise ValueError("No stock data were returned for this request.")

    required = {"date", "price", "daily_return"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    prepared = data.copy()
    prepared["date"] = pd.to_datetime(prepared["date"])
    prepared["price"] = pd.to_numeric(prepared["price"], errors="coerce")
    prepared["daily_return"] = pd.to_numeric(
        prepared["daily_return"],
        errors="coerce",
    )
    prepared = prepared.sort_values("date").dropna(subset=["date", "price"])

    calculated_return = prepared["price"].pct_change()
    prepared["daily_return"] = prepared["daily_return"].fillna(calculated_return)
    prepared = prepared.dropna(subset=["daily_return"]).reset_index(drop=True)

    if prepared.empty:
        raise ValueError("The selected data do not contain enough return observations.")

    prepared["wealth_index"] = (1 + prepared["daily_return"]).cumprod()
    prepared["cumulative_return"] = prepared["wealth_index"] - 1
    prepared["running_peak"] = prepared["wealth_index"].cummax()
    prepared["drawdown"] = prepared["wealth_index"] / prepared["running_peak"] - 1
    return prepared


def calculate_performance_metrics(
    data: pd.DataFrame,
    annual_risk_free_rate: float = 0.02,
) -> dict[str, float]:
    """Calculate return, risk, and Sharpe Ratio metrics."""
    returns = pd.to_numeric(data["daily_return"], errors="coerce").dropna()
    if len(returns) < 2:
        raise ValueError("At least two return observations are required.")

    wealth_index = data["wealth_index"].dropna()
    observation_count = len(returns)
    total_return = float(wealth_index.iloc[-1] - 1)
    annualized_return = float(
        wealth_index.iloc[-1] ** (TRADING_DAYS_PER_YEAR / observation_count) - 1
    )
    annualized_volatility = float(returns.std(ddof=1) * math.sqrt(TRADING_DAYS_PER_YEAR))

    daily_risk_free_rate = (1 + annual_risk_free_rate) ** (
        1 / TRADING_DAYS_PER_YEAR
    ) - 1
    excess_returns = returns - daily_risk_free_rate

    if annualized_volatility == 0 or np.isnan(annualized_volatility):
        sharpe_ratio = np.nan
    else:
        sharpe_ratio = float(
            excess_returns.mean() / returns.std(ddof=1) * math.sqrt(TRADING_DAYS_PER_YEAR)
        )

    return {
        "observations": float(observation_count),
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": float(data["drawdown"].min()),
        "best_daily_return": float(returns.max()),
        "worst_daily_return": float(returns.min()),
        "average_daily_return": float(returns.mean()),
        "win_rate": float((returns > 0).mean()),
    }


def calculate_rolling_metrics(
    data: pd.DataFrame,
    window: int = 63,
    annual_risk_free_rate: float = 0.02,
) -> pd.DataFrame:
    """Calculate rolling volatility and rolling Sharpe Ratio."""
    if window < 2:
        raise ValueError("Rolling window must be at least 2 trading days.")

    result = data[["date", "daily_return"]].copy()
    daily_risk_free_rate = (1 + annual_risk_free_rate) ** (
        1 / TRADING_DAYS_PER_YEAR
    ) - 1
    excess = result["daily_return"] - daily_risk_free_rate
    rolling_std = result["daily_return"].rolling(window).std(ddof=1)

    result["rolling_volatility"] = rolling_std * math.sqrt(TRADING_DAYS_PER_YEAR)
    result["rolling_sharpe"] = (
        excess.rolling(window).mean() / rolling_std * math.sqrt(TRADING_DAYS_PER_YEAR)
    )
    return result

