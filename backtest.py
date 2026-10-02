from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from quant_ai.scoring import calculate_rankings


@dataclass
class BacktestResult:
    portfolio: pd.Series
    benchmark: pd.Series
    metrics: dict[str, float]
    start_date: pd.Timestamp
    end_date: pd.Timestamp


def _rebalance_dates(index: pd.DatetimeIndex, schedule: str) -> pd.DatetimeIndex:
    series = pd.Series(index, index=index)
    dates = series.groupby(index.to_period("Q" if schedule == "Quarterly" else "M")).last()
    return pd.DatetimeIndex(dates.values)


def _metrics(returns: pd.Series, benchmark_returns: pd.Series) -> dict[str, float]:
    returns = returns.dropna()
    wealth = (1 + returns).cumprod()
    benchmark_wealth = (1 + benchmark_returns.reindex(returns.index).fillna(0)).cumprod()
    years = max(len(returns) / 252, 1 / 252)
    volatility = float(returns.std() * np.sqrt(252))
    cagr = float(wealth.iloc[-1] ** (1 / years) - 1)
    drawdown = wealth / wealth.cummax() - 1
    sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() else 0.0
    return {
        "total_return": float(wealth.iloc[-1] - 1),
        "benchmark_return": float(benchmark_wealth.iloc[-1] - 1),
        "cagr": cagr,
        "max_drawdown": float(drawdown.min()),
        "volatility": volatility,
        "sharpe": sharpe,
    }


def run_backtest(
    prices: pd.DataFrame,
    weights: dict[str, float],
    portfolio_size: int = 10,
    rebalance: str = "Monthly",
    transaction_cost_bps: int = 10,
) -> BacktestResult:
    clean = prices.sort_index().ffill(limit=5)
    returns = clean.pct_change(fill_method=None).fillna(0)
    eligible = clean.index[252:]
    dates = _rebalance_dates(pd.DatetimeIndex(eligible), rebalance)
    strategy = pd.Series(0.0, index=clean.index, name="Quant AI")
    previous_holdings: set[str] = set()

    for position, signal_date in enumerate(dates):
        history = clean.loc[:signal_date]
        ranks = calculate_rankings(history, weights)
        holdings = set(ranks.head(portfolio_size).index)
        if not holdings:
            continue
        next_date = dates[position + 1] if position + 1 < len(dates) else clean.index[-1]
        holding_days = clean.index[(clean.index > signal_date) & (clean.index <= next_date)]
        if holding_days.empty:
            continue
        strategy.loc[holding_days] = returns.loc[holding_days, list(holdings)].mean(axis=1)
        turnover = len(holdings.symmetric_difference(previous_holdings)) / max(2 * len(holdings), 1)
        strategy.loc[holding_days[0]] -= turnover * transaction_cost_bps / 10_000
        previous_holdings = holdings

    start = dates[0] if len(dates) else eligible[0]
    strategy = strategy.loc[strategy.index > start]
    benchmark = returns.mean(axis=1).reindex(strategy.index).fillna(0).rename("Equal-weight benchmark")
    portfolio_wealth = 10_000 * (1 + strategy).cumprod()
    benchmark_wealth = 10_000 * (1 + benchmark).cumprod()
    return BacktestResult(
        portfolio=portfolio_wealth,
        benchmark=benchmark_wealth,
        metrics=_metrics(strategy, benchmark),
        start_date=strategy.index[0],
        end_date=strategy.index[-1],
    )

