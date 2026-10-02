from __future__ import annotations

import streamlit as st

from quant_ai.backtest import run_backtest
from quant_ai.data import DEFAULT_TICKERS, load_prices
from quant_ai.scoring import calculate_rankings, stock_explanation
from quant_ai.ui import (
    apply_theme,
    draw_empty_state,
    draw_metric_card,
    draw_page_header,
    format_percent,
    performance_chart,
    price_chart,
    rankings_chart,
)


st.set_page_config(
    page_title="Quant AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


DEFAULTS = {
    "data_mode": "Demo data",
    "tickers": ", ".join(DEFAULT_TICKERS),
    "lookback_12m": 0.55,
    "lookback_6m": 0.30,
    "volatility": 0.15,
    "portfolio_size": 10,
    "transaction_cost_bps": 10,
}
STATE_SCHEMA_VERSION = 2
if st.session_state.get("state_schema_version") != STATE_SCHEMA_VERSION:
    # Reset once after this hotfix so sessions affected by the old widget bug recover automatically.
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.session_state.state_schema_version = STATE_SCHEMA_VERSION
else:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_prices(mode: str, tickers: tuple[str, ...]):
    return load_prices(mode=mode, tickers=list(tickers))


def normalized_weights() -> dict[str, float]:
    raw = {
        "momentum_12m": float(st.session_state.lookback_12m),
        "momentum_6m": float(st.session_state.lookback_6m),
        "volatility": float(st.session_state.volatility),
    }
    total = sum(raw.values()) or 1.0
    return {key: value / total for key, value in raw.items()}


def parse_tickers() -> list[str]:
    raw = st.session_state.tickers.replace("\n", ",")
    return list(dict.fromkeys(item.strip().upper() for item in raw.split(",") if item.strip()))


def restore_starter_settings() -> None:
    """Reset both the model state and the Research Lab editor controls."""
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.session_state.state_schema_version = STATE_SCHEMA_VERSION
    editor_keys = [
        "editor_tickers",
        "editor_lookback_12m",
        "editor_lookback_6m",
        "editor_volatility",
        "editor_portfolio_size",
        "editor_transaction_cost_bps",
    ]
    for key in editor_keys:
        st.session_state.pop(key, None)
    cached_prices.clear()
    st.session_state.pop("backtest_result", None)
    st.session_state.pop("backtest_signature", None)


with st.sidebar:
    st.markdown("<div class='brand'>QUANT <span>AI</span></div>", unsafe_allow_html=True)
    st.caption("Research signals, made understandable · V1.1")
    page = st.radio(
        "Navigation",
        ["Dashboard", "Stock Rankings", "Stock Detail", "Backtester", "Settings / Research Lab"],
        label_visibility="collapsed",
    )
    st.divider()
    st.selectbox("Data source", ["Demo data", "Live market data"], key="data_mode")
    st.caption("Demo mode is synthetic and always available. Live mode uses delayed public prices when available.")
    if st.button("Refresh data", width="stretch"):
        cached_prices.clear()
        st.session_state.pop("backtest_result", None)
        st.session_state.pop("backtest_signature", None)
        st.rerun()
    st.markdown("<div class='safety'>🔒 Research only<br><span>No brokerage connection. No trades are placed.</span></div>", unsafe_allow_html=True)


tickers = parse_tickers()
if len(tickers) < 3:
    st.warning("Add at least three ticker symbols in Settings. Using the default sample list for now.")
    tickers = DEFAULT_TICKERS
st.session_state.portfolio_size = min(max(3, int(st.session_state.portfolio_size)), min(20, len(tickers)))

with st.spinner("Preparing market data…"):
    prices, data_status = cached_prices(st.session_state.data_mode, tuple(tickers))

weights = normalized_weights()
rankings = calculate_rankings(prices, weights)

if data_status.fell_back:
    st.warning(
        "Live prices were unavailable, so the app switched to safe demo data. "
        "Everything remains usable; no action is required."
    )


if page == "Dashboard":
    draw_page_header(
        "Dashboard",
        "A simple view of the current model signals and a sample portfolio—not investment advice.",
        data_status.label,
    )
    if rankings.empty:
        draw_empty_state("Not enough price history to calculate rankings.")
        st.stop()

    result = run_backtest(
        prices,
        weights=weights,
        portfolio_size=min(st.session_state.portfolio_size, max(1, len(rankings))),
        rebalance="Monthly",
        transaction_cost_bps=st.session_state.transaction_cost_bps,
    )

    top = rankings.iloc[0]
    cols = st.columns(4)
    with cols[0]:
        draw_metric_card("Top signal", top.name, f"Score {top['score']:.1f} / 100")
    with cols[1]:
        draw_metric_card("Model return", format_percent(result.metrics["total_return"]), "Full test period")
    with cols[2]:
        draw_metric_card("Benchmark return", format_percent(result.metrics["benchmark_return"]), "Equal-weight universe")
    with cols[3]:
        draw_metric_card("Current basket", str(min(st.session_state.portfolio_size, len(rankings))), "Top-ranked stocks")

    st.markdown("### Growth of $10,000")
    st.plotly_chart(performance_chart(result), width="stretch", config={"displayModeBar": False})

    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("### Current leaders")
        table = rankings.head(8).reset_index(names="Ticker").rename(
            columns={
                "score": "Score",
                "momentum_12m": "12M momentum",
                "momentum_6m": "6M momentum",
                "volatility": "Volatility",
            }
        )
        table.index = table.index + 1
        st.dataframe(
            table[["Ticker", "Score", "12M momentum", "6M momentum", "Volatility"]].style.format(
                {"Score": "{:.1f}", "12M momentum": "{:+.1%}", "6M momentum": "{:+.1%}", "Volatility": "{:.1%}"}
            ),
            width="stretch",
            height=320,
        )
    with right:
        st.markdown("### What the model is doing")
        st.info(
            "The starter model rewards stocks with stronger 12-month and 6-month price momentum, "
            "then subtracts points for higher price volatility. It does not analyze company finances, "
            "news, valuation, taxes, or your personal situation."
        )
        st.markdown("**Current factor mix**")
        st.progress(weights["momentum_12m"], text=f"12-month momentum · {weights['momentum_12m']:.0%}")
        st.progress(weights["momentum_6m"], text=f"6-month momentum · {weights['momentum_6m']:.0%}")
        st.progress(weights["volatility"], text=f"Low-volatility preference · {weights['volatility']:.0%}")


elif page == "Stock Rankings":
    draw_page_header(
        "Stock Rankings",
        "Compare every stock in the research universe. Higher scores indicate stronger model signals.",
        data_status.label,
    )
    if rankings.empty:
        draw_empty_state("Not enough price history to calculate rankings.")
        st.stop()

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        minimum_score = st.slider("Minimum score", 0, 100, 0)
    with c2:
        rows = st.selectbox("Rows to show", [10, 20, 50, "All"], index=1)
    with c3:
        query = st.text_input("Find a ticker", placeholder="Example: MSFT")

    filtered = rankings[rankings["score"] >= minimum_score]
    if query:
        filtered = filtered[filtered.index.str.contains(query.upper(), regex=False)]
    if rows != "All":
        filtered = filtered.head(int(rows))

    if filtered.empty:
        draw_empty_state("No stocks match these filters.")
    else:
        st.plotly_chart(rankings_chart(filtered.head(20)), width="stretch", config={"displayModeBar": False})
        display = filtered.reset_index(names="Ticker")
        display.insert(0, "Rank", range(1, len(display) + 1))
        display = display.rename(
            columns={
                "score": "Score",
                "momentum_12m": "12M momentum",
                "momentum_6m": "6M momentum",
                "volatility": "Volatility",
                "last_price": "Last price",
            }
        )
        st.dataframe(
            display[["Rank", "Ticker", "Score", "12M momentum", "6M momentum", "Volatility", "Last price"]].style.format(
                {"Score": "{:.1f}", "12M momentum": "{:+.1%}", "6M momentum": "{:+.1%}", "Volatility": "{:.1%}", "Last price": "${:,.2f}"}
            ),
            width="stretch",
            hide_index=True,
        )


elif page == "Stock Detail":
    draw_page_header(
        "Stock Detail",
        "See the price history, factor scores, and a plain-English explanation for one stock.",
        data_status.label,
    )
    if rankings.empty:
        draw_empty_state("Not enough price history to show stock details.")
        st.stop()

    selected = st.selectbox("Choose a ticker", rankings.index.tolist())
    row = rankings.loc[selected]
    rank = rankings.index.get_loc(selected) + 1
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        draw_metric_card("Model rank", f"#{rank}", f"of {len(rankings)} stocks")
    with c2:
        draw_metric_card("Overall score", f"{row['score']:.1f}", "out of 100")
    with c3:
        draw_metric_card("12-month momentum", format_percent(row["momentum_12m"]), "Price change")
    with c4:
        draw_metric_card("Annualized volatility", format_percent(row["volatility"]), "Lower is preferred")

    st.markdown(f"### {selected} price history")
    chart_data = prices[[selected]].dropna().tail(504).rename(columns={selected: "Price"})
    st.plotly_chart(price_chart(chart_data, selected), width="stretch", config={"displayModeBar": False})

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("### Why this score?")
        st.success(stock_explanation(selected, row, rank, len(rankings)))
        st.caption("This explanation is generated from the numeric factors—not from news, filings, or an AI opinion.")
    with right:
        st.markdown("### Factor breakdown")
        st.metric("12-month momentum percentile", f"{row['momentum_12m_score']:.0f} / 100")
        st.metric("6-month momentum percentile", f"{row['momentum_6m_score']:.0f} / 100")
        st.metric("Low-volatility percentile", f"{row['volatility_score']:.0f} / 100")


elif page == "Backtester":
    draw_page_header(
        "Backtester",
        "Test how the rules would have behaved in the past. Past results do not predict future returns.",
        data_status.label,
    )
    with st.form("backtest_controls"):
        c1, c2, c3 = st.columns(3)
        with c1:
            portfolio_size = st.slider("Number of stocks", 3, min(20, len(prices.columns)), min(10, len(prices.columns)))
        with c2:
            rebalance = st.selectbox("Rebalance schedule", ["Monthly", "Quarterly"])
        with c3:
            transaction_cost = st.number_input("Estimated trading cost (basis points)", 0, 100, int(st.session_state.transaction_cost_bps), 5)
        submitted = st.form_submit_button("Run backtest", type="primary", width="stretch")

    signature = (
        data_status.label,
        tuple(prices.columns),
        tuple(round(value, 6) for value in weights.values()),
        portfolio_size,
        rebalance,
        transaction_cost,
    )
    if submitted or st.session_state.get("backtest_signature") != signature:
        with st.spinner("Running the historical simulation…"):
            st.session_state.backtest_result = run_backtest(
                prices,
                weights=weights,
                portfolio_size=portfolio_size,
                rebalance=rebalance,
                transaction_cost_bps=transaction_cost,
            )
            st.session_state.backtest_signature = signature
    result = st.session_state.backtest_result

    cols = st.columns(5)
    labels = [
        ("Total return", result.metrics["total_return"]),
        ("Annual return", result.metrics["cagr"]),
        ("Max drawdown", result.metrics["max_drawdown"]),
        ("Volatility", result.metrics["volatility"]),
        ("Sharpe ratio", result.metrics["sharpe"]),
    ]
    for col, (label, value) in zip(cols, labels):
        with col:
            shown = f"{value:.2f}" if label == "Sharpe ratio" else format_percent(value)
            draw_metric_card(label, shown, "Simulated")

    st.plotly_chart(performance_chart(result), width="stretch", config={"displayModeBar": False})
    st.caption(
        f"Test period: {result.start_date:%b %Y} to {result.end_date:%b %Y}. "
        "Signals use only information available before each rebalance. Dividends, taxes, spreads, and market impact are not fully modeled."
    )
    with st.expander("How this backtest works"):
        st.markdown(
            "1. At each rebalance date, the model scores every stock using trailing prices.\n"
            "2. It equally weights the highest-ranked stocks.\n"
            "3. It holds them until the next rebalance and subtracts the trading-cost estimate.\n"
            "4. The benchmark is an equal-weight basket of the available universe, not the S&P 500."
        )


else:
    draw_page_header(
        "Settings / Research Lab",
        "Change the research universe and experiment with factor weights. Nothing here can place a trade.",
        data_status.label,
    )
    st.markdown("### Research universe")
    edited_tickers = st.text_area(
        "Ticker symbols (comma-separated)",
        value=st.session_state.tickers,
        key="editor_tickers",
        height=110,
        help="Live mode attempts to download these symbols. Demo mode creates a stable synthetic history for them.",
    )
    st.session_state.tickers = edited_tickers
    edited_ticker_list = list(
        dict.fromkeys(item.strip().upper() for item in edited_tickers.replace("\n", ",").split(",") if item.strip())
    )
    st.caption(f"{len(edited_ticker_list)} unique symbols selected")

    st.markdown("### Factor weights")
    st.caption("Weights are automatically normalized to 100%.")
    c1, c2, c3 = st.columns(3)
    with c1:
        edited_12m = st.slider(
            "12-month momentum",
            0.0,
            1.0,
            value=float(st.session_state.lookback_12m),
            step=0.05,
            key="editor_lookback_12m",
        )
    with c2:
        edited_6m = st.slider(
            "6-month momentum",
            0.0,
            1.0,
            value=float(st.session_state.lookback_6m),
            step=0.05,
            key="editor_lookback_6m",
        )
    with c3:
        edited_volatility = st.slider(
            "Low-volatility preference",
            0.0,
            1.0,
            value=float(st.session_state.volatility),
            step=0.05,
            key="editor_volatility",
        )
    st.session_state.lookback_12m = edited_12m
    st.session_state.lookback_6m = edited_6m
    st.session_state.volatility = edited_volatility
    mix = normalized_weights()
    st.info(
        f"Current mix: {mix['momentum_12m']:.0%} 12-month momentum · "
        f"{mix['momentum_6m']:.0%} 6-month momentum · {mix['volatility']:.0%} low volatility"
    )

    st.markdown("### Portfolio assumptions")
    c1, c2 = st.columns(2)
    with c1:
        edited_portfolio_size = st.slider(
            "Default portfolio size",
            3,
            min(20, max(3, len(edited_ticker_list))),
            value=min(int(st.session_state.portfolio_size), min(20, max(3, len(edited_ticker_list)))),
            key="editor_portfolio_size",
        )
    with c2:
        edited_transaction_cost = st.number_input(
            "Default trading cost (basis points)",
            0,
            100,
            value=int(st.session_state.transaction_cost_bps),
            step=5,
            key="editor_transaction_cost_bps",
        )
    st.session_state.portfolio_size = edited_portfolio_size
    st.session_state.transaction_cost_bps = edited_transaction_cost

    st.button("Restore starter settings", on_click=restore_starter_settings)

    st.divider()
    st.warning(
        "Important: This is an educational research tool. Scores and simulations are not financial advice. "
        "The app does not know your goals or risk tolerance, and it cannot place real-money trades."
    )

