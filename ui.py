from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from quant_ai.backtest import BacktestResult


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f7f8fc; }
        [data-testid="stSidebar"] { background: #111827; }
        [data-testid="stSidebar"] * { color: #e5e7eb; }
        [data-testid="stSidebar"] .stRadio label { padding: .45rem .6rem; border-radius: .55rem; }
        [data-testid="stSidebar"] .stRadio label:hover { background: #1f2937; }
        [data-testid="stSidebar"] [role="radiogroup"] [aria-checked="true"] { color: #aebcff !important; }
        [data-testid="stSidebar"] [data-baseweb="select"],
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #0b1020 !important; border-color: #334155 !important; color: #f8fafc !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] * {
            background-color: #0b1020 !important; color: #f8fafc !important; fill: #cbd5e1 !important;
        }
        [data-testid="stSidebar"] button {
            background: #1f2937 !important; border-color: #475569 !important; color: #f8fafc !important;
        }
        [data-testid="stSidebar"] button:hover {
            background: #273449 !important; border-color: #64748b !important;
        }
        [data-testid="stSidebar"] button * { color: #f8fafc !important; }
        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] { background: #536dfe; border-color: #536dfe; }
        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover { background: #4259dc; border-color: #4259dc; }
        [data-testid="stSlider"] [role="slider"] { background-color: #536dfe !important; }
        [data-testid="stAlert"] { color: #1f2937 !important; }
        [data-testid="stAlert"] p, [data-testid="stAlert"] div { color: #1f2937 !important; }
        .brand { font-size: 1.55rem; font-weight: 800; letter-spacing: -.04em; color: white; margin-top: .4rem; }
        .brand span { color: #8ea4ff; }
        .safety { background: #172033; border: 1px solid #2d3a52; padding: .85rem; border-radius: .65rem; margin-top: 1rem; font-size: .86rem; }
        .safety span { color: #9ca3af !important; font-size: .76rem; }
        .page-title { font-size: 2.15rem; font-weight: 760; color: #111827; letter-spacing: -.04em; margin-bottom: .15rem; }
        .page-subtitle { color: #64748b; font-size: 1rem; margin-bottom: 1.25rem; }
        .data-pill { display: inline-block; background: #e9efff; color: #3856c8; border-radius: 999px; padding: .3rem .7rem; font-size: .75rem; font-weight: 650; }
        .metric-card { background: white; border: 1px solid #e7eaf1; border-radius: .85rem; padding: 1rem 1.1rem; min-height: 118px; box-shadow: 0 2px 8px rgba(17,24,39,.035); }
        .metric-label { color: #64748b; font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; }
        .metric-value { color: #111827; font-weight: 760; font-size: 1.65rem; margin: .2rem 0; }
        .metric-note { color: #94a3b8; font-size: .78rem; }
        h3 { color: #1f2937; letter-spacing: -.02em; padding-top: .4rem; }
        [data-testid="stDataFrame"] { background: white; border-radius: .7rem; overflow: hidden; }
        .empty-state { background: white; border: 1px dashed #cbd5e1; padding: 2rem; text-align: center; border-radius: .75rem; color: #64748b; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def draw_page_header(title: str, subtitle: str, data_label: str) -> None:
    st.markdown(f"<div class='data-pill'>{data_label}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='page-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='page-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def draw_metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"<div class='metric-card'><div class='metric-label'>{label}</div>"
        f"<div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>",
        unsafe_allow_html=True,
    )


def draw_empty_state(message: str) -> None:
    st.markdown(f"<div class='empty-state'>{message}</div>", unsafe_allow_html=True)


def format_percent(value: float) -> str:
    return f"{value:+.1%}" if pd.notna(value) else "—"


def performance_chart(result: BacktestResult) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=result.portfolio.index, y=result.portfolio, name="Quant AI", line={"color": "#536dfe", "width": 3}))
    figure.add_trace(go.Scatter(x=result.benchmark.index, y=result.benchmark, name="Equal-weight benchmark", line={"color": "#94a3b8", "width": 2}))
    figure.update_layout(
        height=390,
        margin={"l": 15, "r": 15, "t": 25, "b": 15},
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x unified",
        font={"color": "#475569"},
        legend={"orientation": "h", "y": 1.08, "x": 0, "font": {"color": "#334155"}},
        yaxis={"tickprefix": "$", "tickformat": ",.0f", "gridcolor": "#eef0f5", "tickfont": {"color": "#64748b"}},
        xaxis={"gridcolor": "#f6f7f9", "tickfont": {"color": "#64748b"}},
    )
    return figure


def price_chart(chart_data: pd.DataFrame, ticker: str) -> go.Figure:
    figure = go.Figure(
        go.Scatter(
            x=chart_data.index,
            y=chart_data["Price"],
            name=ticker,
            line={"color": "#536dfe", "width": 2.5},
            hovertemplate="%{x|%b %d, %Y}<br>$%{y:,.2f}<extra></extra>",
        )
    )
    figure.update_layout(
        height=390,
        margin={"l": 15, "r": 15, "t": 20, "b": 15},
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x unified",
        showlegend=False,
        font={"color": "#475569"},
        yaxis={"tickprefix": "$", "tickformat": ",.0f", "gridcolor": "#eef0f5", "tickfont": {"color": "#64748b"}},
        xaxis={"gridcolor": "#f6f7f9", "tickfont": {"color": "#64748b"}},
    )
    return figure


def rankings_chart(rankings: pd.DataFrame) -> go.Figure:
    ordered = rankings.sort_values("score")
    figure = go.Figure(go.Bar(
        x=ordered["score"],
        y=ordered.index,
        orientation="h",
        marker={"color": ordered["score"], "colorscale": [[0, "#dce4ff"], [1, "#536dfe"]], "showscale": False},
        hovertemplate="%{y}: %{x:.1f}<extra></extra>",
    ))
    figure.update_layout(
        height=max(330, len(ordered) * 26),
        margin={"l": 15, "r": 15, "t": 10, "b": 15},
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"color": "#475569"},
        xaxis={"range": [0, 100], "title": "Model score", "gridcolor": "#eef0f5", "tickfont": {"color": "#64748b"}},
        yaxis={"title": "", "tickfont": {"color": "#475569"}},
    )
    return figure

