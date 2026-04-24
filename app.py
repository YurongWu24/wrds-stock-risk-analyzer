from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.charts import (
    cumulative_return_chart,
    drawdown_chart,
    price_chart,
    return_distribution_chart,
    rolling_metrics_chart,
)
from src.data_loader import (
    close_wrds_connection,
    connect_to_wrds,
    fetch_daily_stock_data,
    get_latest_crsp_daily_date,
    get_matching_securities,
    get_ticker_history,
)
from src.metrics import (
    calculate_performance_metrics,
    calculate_rolling_metrics,
    prepare_stock_data,
)


st.set_page_config(
    page_title="WRDS Stock Risk Analyzer",
    layout="wide",
)


TERMINAL_CSS = """
<style>
    :root {
        --bg: #071116;
        --panel: #0f1b22;
        --panel-2: #13242d;
        --line: #243540;
        --text: #e6edf3;
        --muted: #9fb1bd;
        --blue: #38bdf8;
        --green: #22c55e;
        --red: #ef4444;
        --amber: #fbbf24;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(56, 189, 248, 0.12), transparent 28rem),
            linear-gradient(180deg, #071116 0%, #0a151b 100%);
        color: var(--text);
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.4rem;
        max-width: 1500px;
    }
    section[data-testid="stSidebar"] {
        background: #08141a;
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        letter-spacing: 0.02em;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(19, 36, 45, 0.96), rgba(11, 24, 31, 0.96));
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 0.72rem 0.82rem;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.24);
        min-height: 5.2rem;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    div[data-testid="stMetricValue"] {
        color: var(--text);
        font-size: 1.55rem;
        line-height: 1.2;
    }
    div[data-testid="stPlotlyChart"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        box-sizing: border-box;
        padding: 0.45rem;
        overflow: hidden;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.24);
    }
    div[data-testid="stPlotlyChart"] > div {
        border-radius: 4px;
        overflow: hidden;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.7rem;
    }
    .terminal-header {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        border-bottom: 1px solid var(--line);
        padding: 0.2rem 0 0.85rem 0;
        margin-bottom: 0.65rem;
    }
    .terminal-kicker {
        color: var(--blue);
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .terminal-title {
        color: var(--text);
        font-size: 2.0rem;
        font-weight: 760;
        line-height: 1.08;
        margin-top: 0.1rem;
    }
    .terminal-subtitle {
        color: var(--muted);
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }
    .terminal-badge {
        border: 1px solid rgba(56, 189, 248, 0.42);
        background: rgba(56, 189, 248, 0.10);
        color: #b9ecff;
        border-radius: 999px;
        padding: 0.46rem 0.72rem;
        font-size: 0.78rem;
        white-space: nowrap;
    }
    .source-strip {
        display: grid;
        grid-template-columns: 1.2fr 0.85fr 0.7fr 0.65fr 0.8fr;
        gap: 0.55rem;
        margin: 0.35rem 0 0.45rem 0;
    }
    .source-item {
        background: rgba(15, 27, 34, 0.92);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 0.58rem 0.72rem;
    }
    .source-label {
        color: var(--muted);
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .source-value {
        color: var(--text);
        font-size: 0.91rem;
        margin-top: 0.1rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .section-title {
        color: var(--text);
        font-size: 1.02rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin: 0.15rem 0 0.1rem 0;
    }
    @media (max-width: 900px) {
        .terminal-header {
            align-items: flex-start;
            flex-direction: column;
        }
        .source-strip {
            grid-template-columns: 1fr;
        }
    }
</style>
"""


PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


def format_percent(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:,.2f}%"


def format_number(value: float, digits: int = 2) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{digits}f}"


def reset_analysis_state() -> None:
    for key in ["stock_data", "rolling_data", "metrics", "security", "query"]:
        st.session_state.pop(key, None)


st.markdown(TERMINAL_CSS, unsafe_allow_html=True)
st.markdown(
    """
    <div class="terminal-header">
        <div>
            <div class="terminal-kicker">WRDS CRSP CIZ Terminal</div>
            <div class="terminal-title">Stock Risk and Return Analyzer</div>
            <div class="terminal-subtitle">ACC102 Track 4 Interactive Data Analysis Tool</div>
        </div>
        <div class="terminal-badge">WRDS credentials required</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("WRDS Login")
    username = st.text_input(
        "Username",
        value=st.session_state.get("wrds_username", ""),
    )
    password = st.text_input("Password", type="password")

    if st.button("Connect", use_container_width=True):
        try:
            close_wrds_connection(st.session_state.get("wrds_conn"))
            with st.spinner("Connecting to WRDS..."):
                conn = connect_to_wrds(username, password)
                st.session_state["wrds_conn"] = conn
            with st.spinner("Checking CRSP daily data coverage..."):
                st.session_state["latest_crsp_date"] = get_latest_crsp_daily_date(conn)
            st.session_state["wrds_username"] = username.strip()
            st.session_state["connected"] = True
            reset_analysis_state()
            st.success("Connected.")
        except Exception as exc:
            st.session_state["connected"] = False
            st.error(f"Connection failed: {exc}")

    if st.session_state.get("connected"):
        st.success(f"Active WRDS user: {st.session_state.get('wrds_username')}")
        latest_crsp_date = st.session_state.get("latest_crsp_date")
        if latest_crsp_date:
            st.caption(f"Latest available CRSP daily date: {latest_crsp_date}")
        if st.button("Disconnect", use_container_width=True):
            close_wrds_connection(st.session_state.get("wrds_conn"))
            st.session_state.clear()
            st.rerun()

    st.divider()
    st.header("Analysis Inputs")
    ticker = st.text_input("Ticker", value="AAPL", max_chars=12).strip().upper()
    latest_crsp_date = st.session_state.get("latest_crsp_date")
    default_end = latest_crsp_date or date.today()
    default_start = default_end - timedelta(days=365 * 3)
    start_date = st.date_input("Start date", value=default_start, key="start_date")
    end_date = st.date_input("End date", value=default_end, key="end_date")
    if latest_crsp_date and end_date > latest_crsp_date:
        st.warning(
            f"Selected end date is after WRDS CRSP coverage. "
            f"The app will use {latest_crsp_date}."
        )
    annual_risk_free_rate = st.number_input(
        "Annual risk-free rate",
        min_value=0.0,
        max_value=0.20,
        value=0.02,
        step=0.005,
        format="%.3f",
    )
    rolling_window = st.slider(
        "Rolling window",
        min_value=21,
        max_value=252,
        value=63,
        step=21,
    )
    run_analysis = st.button("Load WRDS Data", type="primary", use_container_width=True)

if not st.session_state.get("connected"):
    st.warning("A valid WRDS account is required before the analysis can run.")
    st.stop()

if run_analysis:
    if not ticker:
        st.error("Please enter a ticker.")
        st.stop()
    if start_date >= end_date:
        st.error("Start date must be earlier than end date.")
        st.stop()
    latest_crsp_date = st.session_state.get("latest_crsp_date")
    effective_end_date = min(end_date, latest_crsp_date) if latest_crsp_date else end_date
    if latest_crsp_date and start_date > latest_crsp_date:
        st.error(
            f"Start date is after the latest available CRSP daily date "
            f"({latest_crsp_date}). Please choose an earlier date."
        )
        st.stop()
    if start_date >= effective_end_date:
        st.error("The selected date range does not overlap available WRDS CRSP data.")
        st.stop()

    try:
        conn = st.session_state["wrds_conn"]
        with st.spinner("Searching CRSP securities..."):
            matches = get_matching_securities(conn, ticker, start_date, effective_end_date)

        if matches.empty:
            history = get_ticker_history(conn, ticker)
            st.error("No common-share CRSP security matched this ticker and date range.")
            if history.empty:
                st.info(
                    "WRDS returned no CRSP stock-name record for this ticker. "
                    "Please check the ticker spelling or try another listed stock."
                )
            else:
                st.info(
                    "WRDS found CIZ ticker records, but none matched both the selected "
                    "date range and the common-share filters used by CRSP CIZ. "
                    "Try a date range that overlaps one of the records below."
                )
                st.dataframe(history, use_container_width=True, hide_index=True)
            st.stop()

        security = matches.iloc[0].to_dict()
        with st.spinner("Downloading daily stock data from WRDS..."):
            raw_data = fetch_daily_stock_data(
                conn,
                int(security["permno"]),
                start_date,
                effective_end_date,
            )
            stock_data = prepare_stock_data(raw_data)
            rolling_data = calculate_rolling_metrics(
                stock_data,
                window=rolling_window,
                annual_risk_free_rate=annual_risk_free_rate,
            )
            metrics = calculate_performance_metrics(
                stock_data,
                annual_risk_free_rate=annual_risk_free_rate,
            )

        st.session_state["stock_data"] = stock_data
        st.session_state["rolling_data"] = rolling_data
        st.session_state["metrics"] = metrics
        st.session_state["security"] = security
        st.session_state["query"] = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": effective_end_date,
            "requested_end_date": end_date,
            "annual_risk_free_rate": annual_risk_free_rate,
            "rolling_window": rolling_window,
        }
        st.success("Data loaded and metrics calculated.")
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")

if "stock_data" not in st.session_state:
    st.info("Enter a ticker and date range, then load data from WRDS.")
    st.stop()

stock_data = st.session_state["stock_data"]
rolling_data = st.session_state["rolling_data"]
metrics = st.session_state["metrics"]
security = st.session_state["security"]
query = st.session_state["query"]
latest_source_date = st.session_state.get("latest_crsp_date", "Unknown")

st.markdown(
    f"""
    <div class="source-strip">
        <div class="source-item">
            <div class="source-label">Instrument</div>
            <div class="source-value">{query['ticker']} | {security.get('comnam', 'Selected security')}</div>
        </div>
        <div class="source-item">
            <div class="source-label">WRDS dataset</div>
            <div class="source-value">CRSP Flat File 2.0 / CIZ</div>
        </div>
        <div class="source-item">
            <div class="source-label">Latest WRDS date</div>
            <div class="source-value">{latest_source_date}</div>
        </div>
        <div class="source-item">
            <div class="source-label">Security ID</div>
            <div class="source-value">PERMNO {int(security['permno'])}</div>
        </div>
        <div class="source-item">
            <div class="source-label">Analysis window</div>
            <div class="source-value">{query['start_date']} to {query['end_date']}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(5)
metric_cols[0].metric("Total return", format_percent(metrics["total_return"]))
metric_cols[1].metric(
    "Annualized return",
    format_percent(metrics["annualized_return"]),
)
metric_cols[2].metric(
    "Annualized volatility",
    format_percent(metrics["annualized_volatility"]),
)
metric_cols[3].metric("Sharpe Ratio", format_number(metrics["sharpe_ratio"]))
metric_cols[4].metric("Max drawdown", format_percent(metrics["max_drawdown"]))

detail_cols = st.columns(4)
detail_cols[0].metric("Trading days", format_number(metrics["observations"], 0))
detail_cols[1].metric("Win rate", format_percent(metrics["win_rate"]))
detail_cols[2].metric("Best day", format_percent(metrics["best_daily_return"]))
detail_cols[3].metric("Worst day", format_percent(metrics["worst_daily_return"]))

st.markdown('<div class="section-title">Market Analysis</div>', unsafe_allow_html=True)
top_left, top_right = st.columns([1.55, 1], gap="small")
with top_left:
    st.plotly_chart(
        price_chart(stock_data),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )
with top_right:
    st.plotly_chart(
        cumulative_return_chart(stock_data),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

bottom_left, bottom_mid, bottom_right = st.columns([1, 1, 1.28], gap="small")
with bottom_left:
    st.plotly_chart(
        return_distribution_chart(stock_data),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )
with bottom_mid:
    st.plotly_chart(
        drawdown_chart(stock_data),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )
with bottom_right:
    st.plotly_chart(
        rolling_metrics_chart(rolling_data),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

with st.expander("WRDS CIZ observations", expanded=False):
    display_columns = [
        "date",
        "permno",
        "price",
        "daily_return",
        "volume",
        "market_cap_millions",
        "cumulative_return",
        "drawdown",
    ]
    st.dataframe(
        stock_data[[column for column in display_columns if column in stock_data.columns]],
        use_container_width=True,
        hide_index=True,
    )
