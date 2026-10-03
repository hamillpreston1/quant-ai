from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from quant_ai.scoring import calculate_rankings


@dataclass
class BacktestResult:
    portfolio: pd.Series
    benchmark: pd.Series
    benchmark_name: str
    metrics: dict[str, float]
    holdings: pd.DataFrame
    rebalances: pd.DataFrame
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
    benchmark_cagr = float(benchmark_wealth.iloc[-1] ** (1 / years) - 1)
    drawdown = wealth / wealth.cummax() - 1
    benchmark_drawdown = benchmark_wealth / benchmark_wealth.cummax() - 1
    sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() else 0.0
    return {
        "total_return": float(wealth.iloc[-1] - 1),
        "benchmark_return": float(benchmark_wealth.iloc[-1] - 1),
        "benchmark_cagr": benchmark_cagr,
        "benchmark_max_drawdown": float(benchmark_drawdown.min()),
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
    benchmark_prices: pd.Series | None = None,
    benchmark_name: str = "SPY",
    start_date: pd.Timestamp | None = None,
    end_date: pd.Timestamp | None = None,
) -> BacktestResult:
    clean = prices.sort_index().ffill(limit=5)
    returns = clean.pct_change(fill_method=None).fillna(0)
    end_timestamp = pd.Timestamp(end_date) if end_date is not None else clean.index[-1]
    start_timestamp = pd.Timestamp(start_date) if start_date is not None else clean.index[252]
    eligible = clean.index[(clean.index >= start_timestamp) & (clean.index <= end_timestamp)]
    if len(eligible) < 2:
        raise ValueError("The selected date range is too short for a backtest.")
    dates = _rebalance_dates(pd.DatetimeIndex(eligible), rebalance)
    if len(dates) == 0:
        raise ValueError("No rebalance dates are available in the selected range.")
    strategy = pd.Series(0.0, index=clean.index, name="Quant AI")
    previous_holdings: set[str] = set()
    holdings_rows: list[dict[str, object]] = []
    rebalance_rows: list[dict[str, object]] = []

    for position, signal_date in enumerate(dates):
        history = clean.loc[:signal_date]
        ranks = calculate_rankings(history, weights)
        selected = ranks.head(portfolio_size)
        holdings = set(selected.index)
        if not holdings:
            continue
        next_date = dates[position + 1] if position + 1 < len(dates) else end_timestamp
        holding_days = clean.index[
            (clean.index > signal_date) & (clean.index <= next_date) & (clean.index <= end_timestamp)
        ]
        if holding_days.empty:
            continue
        strategy.loc[holding_days] = returns.loc[holding_days, list(holdings)].mean(axis=1)
        turnover = 1.0 if not previous_holdings else len(holdings.symmetric_difference(previous_holdings)) / max(2 * len(holdings), 1)
        strategy.loc[holding_days[0]] -= turnover * transaction_cost_bps / 10_000
        added = sorted(holdings - previous_holdings)
        removed = sorted(previous_holdings - holdings)
        rebalance_rows.append(
            {
                "Rebalance date": signal_date,
                "Holdings": ", ".join(selected.index),
                "Added": ", ".join(added) if added else "—",
                "Removed": ", ".join(removed) if removed else "—",
                "Turnover": turnover,
            }
        )
        for rank, (ticker, row) in enumerate(selected.iterrows(), start=1):
            holdings_rows.append(
                {
                    "Rebalance date": signal_date,
                    "Rank": rank,
                    "Ticker": ticker,
                    "Score": float(row["score"]),
                    "12M momentum": float(row["momentum_12m"]),
                    "6M momentum": float(row["momentum_6m"]),
                    "Volatility": float(row["volatility"]),
                }
            )
        previous_holdings = holdings

    start = dates[0] if len(dates) else eligible[0]
    strategy = strategy.loc[(strategy.index > start) & (strategy.index <= end_timestamp)]
    if strategy.empty:
        raise ValueError("The selected date range did not produce any holding days.")
    if benchmark_prices is None:
        benchmark_returns = returns.mean(axis=1)
        benchmark_name = "Equal-weight universe"
    else:
        benchmark_returns = benchmark_prices.sort_index().ffill(limit=5).pct_change(fill_method=None)
    benchmark = benchmark_returns.reindex(strategy.index).fillna(0).rename(benchmark_name)
    portfolio_wealth = 10_000 * (1 + strategy).cumprod()
    benchmark_wealth = 10_000 * (1 + benchmark).cumprod()
    return BacktestResult(
        portfolio=portfolio_wealth,
        benchmark=benchmark_wealth,
        benchmark_name=benchmark_name,
        metrics=_metrics(strategy, benchmark),
        holdings=pd.DataFrame(holdings_rows),
        rebalances=pd.DataFrame(rebalance_rows),
        start_date=strategy.index[0],
        end_date=strategy.index[-1],
    )

