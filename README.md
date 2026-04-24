# WRDS Stock Risk and Return Analyzer

ACC102 Track 4 Interactive Data Analysis Tool

Live app: https://wrds-stock-risk-analyzer-5v43uzefpj44e4ormdx9vg.streamlit.app/

## Project overview

This project is a local Streamlit app for beginner-level stock risk and return analysis. A user enters a stock ticker, date range, annual risk-free rate, and rolling window. The app connects to WRDS with the user's own WRDS credentials, retrieves CRSP daily stock data, cleans the data, calculates key quantitative indicators, and presents interactive charts.

The app is designed for finance, accounting, and business students who want a simple way to understand how a stock performed over a selected period.

## Analytical problem

The main question is:

How can an introductory finance user quickly evaluate the historical return, risk, Sharpe Ratio, and drawdown profile of a listed stock using WRDS data?

The app focuses on practical interpretation rather than advanced modelling. It turns raw daily stock records into indicators that are easier to compare and explain.

## Data source

The project uses WRDS CRSP Flat File Format 2.0 (CIZ) daily stock data:

- `crsp.dsf_v2` for ticker-to-PERMNO matching and daily stock price, return, volume, shares outstanding, and market capitalization

WRDS credentials are required. This repository does not include WRDS data because WRDS data are access-controlled and should not be redistributed through a public GitHub repository.

Credentials are entered at runtime in the Streamlit sidebar. The app does not save the username or password to a file.

## Main methods

- Connect to WRDS using the `wrds` Python package
- Match user-entered ticker symbols to CRSP CIZ securities
- Retrieve daily stock data for the selected date range
- Clean prices, returns, volume, and shares outstanding
- Calculate cumulative return, annualized return, annualized volatility, Sharpe Ratio, maximum drawdown, win rate, best day, and worst day
- Visualize price, cumulative return, return distribution, drawdown, rolling volatility, and rolling Sharpe Ratio

## Repository structure

```text
task4/
  app.py
  src/
    data_loader.py
    metrics.py
    charts.py
  notebooks/
    analysis_workflow.ipynb
  README.md
  requirements.txt
```

## How to run locally

Use these commands from inside the project folder.

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## How to use the app

1. Run the Streamlit app locally.
2. Enter a valid WRDS username and password in the sidebar.
3. Check the latest available CRSP daily date shown in the sidebar.
4. Enter a ticker, date range, annual risk-free rate, and rolling window.
5. Click **Load WRDS Data**.
6. Review the performance metrics and interactive charts.

## Limitations

- The app requires WRDS access, so users without a WRDS account cannot retrieve data.
- WRDS CRSP data are historical research data, not real-time market quotes. The latest available date depends on the user's WRDS subscription and CRSP CIZ update schedule.
- The app currently analyses one ticker at a time.
- Ticker symbols can be reused over time, so the app selects the most recent matching common-share CRSP security in the chosen date range.
- Sharpe Ratio is based on historical daily returns and should not be interpreted as a forecast.
- Corporate events and delisting returns may require more advanced treatment in a professional analysis.
