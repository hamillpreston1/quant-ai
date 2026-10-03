from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


DEFAULT_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "BRK-B", "LLY", "AVGO", "JPM",
    "V", "XOM", "UNH", "COST", "MA", "HD", "PG", "NFLX", "CRM", "AMD",
]


@dataclass(frozen=True)
class DataStatus:
    label: str
    benchmark_label: str
    fell_back: bool = False


def generate_demo_market(tickers: list[str], years: int = 7) -> tuple[pd.DataFrame, pd.Series]:
    """Create deterministic, market-like synthetic prices for safe UI exploration."""
    end = pd.Timestamp.today().normalize()
    dates = pd.bdate_range(end=end, periods=years * 252)
    market_rng = np.random.default_rng(20261001)
    market = market_rng.normal(0.00032, 0.009, len(dates))
    output: dict[str, np.ndarray] = {}

    for index, ticker in enumerate(tickers):
        seed = sum((position + 1) * ord(char) for position, char in enumerate(ticker)) + 7301
        rng = np.random.default_rng(seed)
        drift = 0.00008 + (index % 9) * 0.000045
        beta = 0.65 + (index % 6) * 0.10
        idiosyncratic_vol = 0.006 + (index % 7) * 0.0012
        cycle = np.sin(np.linspace(0, 5 * np.pi, len(dates)) + index) * 0.00045
        returns = drift + beta * market + cycle + rng.normal(0, idiosyncratic_vol, len(dates))
        start_price = 45 + (index * 13) % 180
        output[ticker] = start_price * np.exp(np.cumsum(returns))

    benchmark_rng = np.random.default_rng(8675309)
    benchmark_returns = 0.00018 + 0.95 * market + benchmark_rng.normal(0, 0.0025, len(dates))
    benchmark = pd.Series(100 * np.exp(np.cumsum(benchmark_returns)), index=dates, name="Synthetic SPY proxy")
    return pd.DataFrame(output, index=dates), benchmark


def generate_demo_prices(tickers: list[str], years: int = 7) -> pd.DataFrame:
    """Backward-compatible helper returning only the synthetic stock universe."""
    prices, _ = generate_demo_market(tickers, years)
    return prices


def download_live_prices(tickers: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Download adjusted public prices. Import is delayed so demo mode has no network dependency."""
    import yfinance as yf

    symbols = list(dict.fromkeys([*tickers, "SPY"]))
    raw = yf.download(
        tickers=symbols,
        period="7y",
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
        timeout=12,
    )
    if raw.empty:
        raise ValueError("The market-data provider returned no prices.")

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw.xs("Close", axis=1, level=1)
    else:
        prices = raw[["Close"]].rename(columns={"Close": symbols[0]})

    prices = prices.reindex(columns=symbols).sort_index().ffill(limit=5)
    benchmark = prices["SPY"].dropna().rename("SPY")
    universe = prices.reindex(columns=tickers)
    universe = universe.dropna(axis=1, thresh=max(252, int(len(universe) * 0.6)))
    if universe.shape[1] < 3:
        raise ValueError("Fewer than three symbols had enough usable history.")
    if len(benchmark) < 252:
        raise ValueError("SPY did not have enough usable benchmark history.")
    return universe, benchmark


def load_prices(mode: str, tickers: list[str]) -> tuple[pd.DataFrame, pd.Series, DataStatus]:
    if mode == "Live market data":
        try:
            prices, benchmark = download_live_prices(tickers)
            return prices, benchmark, DataStatus("Live public prices", "SPY")
        except Exception:
            prices, benchmark = generate_demo_market(tickers)
            return prices, benchmark, DataStatus("Demo fallback", "Synthetic SPY proxy", fell_back=True)
    prices, benchmark = generate_demo_market(tickers)
    return prices, benchmark, DataStatus("Safe demo data", "Synthetic SPY proxy")

