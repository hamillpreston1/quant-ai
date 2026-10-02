# Quant AI V1.1 hotfix deployment

This update fixes the Research Lab state-reset bug and improves visual consistency.

## Upload the update

1. Unzip `Quant_AI_V1.1_Hotfix.zip`.
2. Open your `quant-ai` repository on GitHub.
3. Choose **Add file → Upload files**.
4. Upload the contents inside the unzipped `quant_ai_streamlit` folder. Replace files when GitHub shows matching names.
5. Enter the commit message `Deploy Quant AI V1.1 hotfix`.
6. Click **Commit changes**.
7. Wait one or two minutes and refresh your Streamlit app.

Streamlit normally deploys the commit automatically. If the old version remains, open `share.streamlit.io`, use the three-dot menu beside the app, and select **Reboot**.

## Important theme check

In GitHub, confirm that the repository contains `.streamlit/config.toml`. The folder name begins with a dot. If it is missing:

1. Choose **Add file → Create new file**.
2. Enter `.streamlit/config.toml` as the filename.
3. Copy the contents of `.streamlit/config.toml` from the hotfix package into the editor.
4. Commit the new file.

The app now has CSS fallbacks for the most important colors, so it remains readable even if the theme file is accidentally omitted.

## Verify the hotfix

1. Open **Settings / Research Lab**.
2. Confirm the ticker list is populated.
3. Confirm the factor sliders show `0.55`, `0.30`, and `0.15`.
4. Confirm the trading-cost field shows `10`.
5. Return to **Dashboard**.
6. Confirm the top signal has a non-zero score and the factor mix remains 55% / 30% / 15%.

If those checks pass, the hotfix is live.
