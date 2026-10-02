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
    fell_back: bool = False


def generate_demo_prices(tickers: list[str], years: int = 7) -> pd.DataFrame:
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

    return pd.DataFrame(output, index=dates)


def download_live_prices(tickers: list[str]) -> pd.DataFrame:
    """Download adjusted public prices. Import is delayed so demo mode has no network dependency."""
    import yfinance as yf

    raw = yf.download(
        tickers=tickers,
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
        prices = raw[["Close"]].rename(columns={"Close": tickers[0]})

    prices = prices.reindex(columns=tickers).sort_index().ffill(limit=5)
    prices = prices.dropna(axis=1, thresh=max(252, int(len(prices) * 0.6)))
    if prices.shape[1] < 3:
        raise ValueError("Fewer than three symbols had enough usable history.")
    return prices


def load_prices(mode: str, tickers: list[str]) -> tuple[pd.DataFrame, DataStatus]:
    if mode == "Live market data":
        try:
            return download_live_prices(tickers), DataStatus("Live public prices")
        except Exception:
            return generate_demo_prices(tickers), DataStatus("Demo fallback", fell_back=True)
    return generate_demo_prices(tickers), DataStatus("Safe demo data")

