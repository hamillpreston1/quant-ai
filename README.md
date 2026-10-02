# Quant AI — User-Friendly Starter App

**Version 1.1:** Fixes Research Lab settings persistence, improves chart and alert contrast, and makes the purple theme more resilient on Community Cloud.

Quant AI is a browser-based research app for exploring a simple stock-ranking strategy. It rewards stronger 12-month and 6-month momentum and penalizes higher volatility.

It includes:

- a clean dashboard
- sortable stock rankings
- plain-English stock detail pages
- an interactive historical backtester
- a Research Lab for changing tickers and factor weights
- built-in synthetic demo data
- optional public market-price downloads with automatic demo fallback

> **Safety note:** This is an educational research tool, not financial advice. It does not connect to a brokerage and cannot place trades. Demo data is synthetic. Historical results do not predict future performance.

## Easiest option: put it online with Streamlit Community Cloud

You do not need to know how to code.

1. Create a free account at [GitHub](https://github.com/signup).
2. On GitHub, click **New repository**.
3. Name it `quant-ai`, choose **Public**, and click **Create repository**.
4. Unzip this download on your computer.
5. In the new GitHub repository, click **Add file → Upload files**.
6. Upload **the contents inside the `quant_ai_streamlit` folder**. Make sure `app.py` and `requirements.txt` are at the top level of the repository.
7. Click **Commit changes**.
8. Create a free account at [Streamlit Community Cloud](https://share.streamlit.io/) using your GitHub account.
9. Click **Create app**, choose your `quant-ai` repository, and set the main file to `app.py`.
10. Click **Deploy**. After a few minutes, Streamlit will give you a web address that you can bookmark and share.

The app starts in **Demo data** mode, so it works even when the market-data provider is unavailable. Use the sidebar to switch to **Live market data**.

## Run it on your own computer (optional)

Only use this route if you are comfortable installing Python.

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/).
2. Open a terminal inside the unzipped `quant_ai_streamlit` folder.
3. Install the required packages:

   ```text
   python -m pip install -r requirements.txt
   ```

4. Start the app:

   ```text
   python -m streamlit run app.py
   ```

5. Your browser should open automatically. If it does not, visit `http://localhost:8501`.

## How to use the app

- **Dashboard:** See the current leaders and the starter strategy at a glance.
- **Stock Rankings:** Filter and compare all stocks in the selected universe.
- **Stock Detail:** Pick one ticker to see its history and understand its score.
- **Backtester:** Choose a portfolio size and rebalance schedule, then run a simulation.
- **Settings / Research Lab:** Change ticker symbols and factor weights without editing code.

## What this first version does—and does not do

The score combines three price-based signals:

- 55% 12-month momentum
- 30% 6-month momentum
- 15% preference for lower volatility

You can change those weights in the Research Lab. The backtest uses information available before each rebalance and includes a simple trading-cost estimate.

This version does **not** include fundamentals, SEC filings, earnings-call analysis, survivorship-bias-free historical membership, taxes, full dividend modeling, or real trading. Those are later-stage improvements after the user experience and testing process are stable.

## Troubleshooting

- **The app says it switched to demo data:** The public data service was unavailable or did not return enough history. Keep exploring normally or try **Refresh data** later.
- **A ticker is missing:** Check the symbol in Settings. Some symbols use a dash on Yahoo Finance, such as `BRK-B`.
- **The app will not deploy:** Confirm that `app.py` and `requirements.txt` are at the top level of the GitHub repository—not inside an extra folder.
- **The first load feels slow:** Live data downloads can take several seconds. The app caches results for one hour.

## Suggested next milestone

Use the app in Demo mode first, deploy it, and make a short list of anything that feels confusing. After that, the most important quantitative improvement is adding a trustworthy historical stock universe to reduce survivorship bias before interpreting backtest results seriously.

