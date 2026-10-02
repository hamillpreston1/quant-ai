from __future__ import annotations

import pandas as pd


def _percentile(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    clean = series.dropna()
    if clean.empty:
        return pd.Series(index=series.index, dtype=float)
    ranked = clean.rank(pct=True, ascending=higher_is_better) * 100
    return ranked.reindex(series.index)


def calculate_rankings(prices: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    clean = prices.sort_index().ffill(limit=5)
    if len(clean) < 253:
        return pd.DataFrame()

    daily_returns = clean.pct_change(fill_method=None)
    factors = pd.DataFrame(index=clean.columns)
    factors["momentum_12m"] = clean.iloc[-1] / clean.iloc[-252] - 1
    factors["momentum_6m"] = clean.iloc[-1] / clean.iloc[-126] - 1
    factors["volatility"] = daily_returns.tail(252).std() * (252**0.5)
    factors["last_price"] = clean.iloc[-1]
    factors = factors.dropna()

    factors["momentum_12m_score"] = _percentile(factors["momentum_12m"], True)
    factors["momentum_6m_score"] = _percentile(factors["momentum_6m"], True)
    factors["volatility_score"] = _percentile(factors["volatility"], False)
    factors["score"] = (
        factors["momentum_12m_score"] * weights["momentum_12m"]
        + factors["momentum_6m_score"] * weights["momentum_6m"]
        + factors["volatility_score"] * weights["volatility"]
    )
    return factors.sort_values(["score", "momentum_12m"], ascending=False)


def stock_explanation(ticker: str, row: pd.Series, rank: int, total: int) -> str:
    strengths: list[str] = []
    cautions: list[str] = []
    if row["momentum_12m_score"] >= 70:
        strengths.append("strong 12-month price momentum")
    elif row["momentum_12m_score"] <= 30:
        cautions.append("weak 12-month momentum")
    if row["momentum_6m_score"] >= 70:
        strengths.append("strong recent momentum")
    elif row["momentum_6m_score"] <= 30:
        cautions.append("weak recent momentum")
    if row["volatility_score"] >= 70:
        strengths.append("relatively steady price movement")
    elif row["volatility_score"] <= 30:
        cautions.append("higher-than-average volatility")

    strength_text = ", ".join(strengths) if strengths else "a balanced mix of factor readings"
    caution_text = f" The main caution is {', and '.join(cautions)}." if cautions else " No factor is an obvious outlier on the downside."
    return (
        f"{ticker} ranks #{rank} of {total}. Its score is mainly supported by {strength_text}."
        f"{caution_text} This is a statistical signal, not a prediction that the stock will rise."
    )

