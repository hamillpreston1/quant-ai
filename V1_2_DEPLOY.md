# Deploy Quant AI V1.2

This update adds the Trust Layer: an SPY benchmark, selectable backtest dates, rebalance and holdings history, and downloadable results.

## Upload the update

1. Unzip `Quant_AI_V1.2_Trust_Layer.zip`.
2. Open your existing `quant-ai` repository on GitHub.
3. Choose **Add file → Upload files**.
4. Upload everything inside the unzipped `quant_ai_streamlit` folder.
5. Allow GitHub to replace files with matching names.
6. Enter the commit message `Deploy Quant AI V1.2 Trust Layer`.
7. Click **Commit changes**.
8. Wait about two minutes, then refresh your Streamlit app.

Streamlit Community Cloud normally redeploys automatically after the GitHub commit. If the old version remains, open your app dashboard at `share.streamlit.io`, use the app menu, and choose **Reboot**.

## Confirm V1.2 is live

1. Look under the Quant AI logo and confirm it says **V1.2**.
2. Open **Backtester**.
3. Confirm you can select a backtest start date and end date.
4. Run the backtest and confirm the chart names **SPY** in Live mode or **Synthetic SPY proxy** in Demo mode.
5. Open both **Rebalance summary** and **Position-level holdings**.
6. Confirm the three download buttons appear below the tables.

No brokerage connection was added. The app remains research-only and cannot place trades.
