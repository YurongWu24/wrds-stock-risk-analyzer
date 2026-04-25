"""Plotly chart builders for the Streamlit app."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


COLOR_BG = "#FFFFFF"
COLOR_PANEL = "#FFFFFF"
COLOR_GRID = "#E5E7EB"
COLOR_TEXT = "#111827"
COLOR_MUTED = "#6B7280"
COLOR_PRICE = "#38BDF8"
COLOR_RETURN = "#2DD4BF"
COLOR_RISK = "#A78BFA"
COLOR_DRAWDOWN = "#F97316"
COLOR_UP = "#22C55E"
COLOR_DOWN = "#EF4444"
COLOR_AVERAGE = "#FBBF24"


def _apply_layout(fig: go.Figure, y_title: str, height: int = 320) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLOR_PANEL,
        plot_bgcolor=COLOR_PANEL,
        font=dict(color=COLOR_TEXT, size=12),
        title=dict(font=dict(size=15, color=COLOR_TEXT), x=0.02),
        margin=dict(l=22, r=22, t=50, b=46),
        hovermode="x unified",
        yaxis_title=y_title,
        xaxis_title=None,
        legend_title_text=None,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        height=height,
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLOR_GRID,
        zeroline=False,
        color=COLOR_MUTED,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLOR_GRID,
        zeroline=False,
        color=COLOR_MUTED,
    )
    return fig


def price_chart(data: pd.DataFrame) -> go.Figure:
    chart_data = data.sort_values("date").copy()
    chart_data["trend"] = "Flat"
    chart_data.loc[chart_data["daily_return"] > 0, "trend"] = "Up day"
    chart_data.loc[chart_data["daily_return"] < 0, "trend"] = "Down day"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=chart_data["date"],
            y=chart_data["price"],
            mode="lines",
            name="Price",
            line=dict(color=COLOR_PRICE, width=2.2),
        )
    )
    if len(chart_data) >= 20:
        fig.add_trace(
            go.Scatter(
                x=chart_data["date"],
                y=chart_data["price"].rolling(20).mean(),
                mode="lines",
                name="20-day average",
                line=dict(color=COLOR_AVERAGE, width=1.4, dash="dot"),
            )
        )
    for trend, color in [("Up day", COLOR_UP), ("Down day", COLOR_DOWN)]:
        subset = chart_data[chart_data["trend"] == trend]
        if not subset.empty:
            fig.add_trace(
                go.Scatter(
                    x=subset["date"],
                    y=subset["price"],
                    mode="markers",
                    name=trend,
                    marker=dict(color=color, size=4.5, opacity=0.78),
                )
            )
    fig.update_layout(title="Price Trend by Daily Direction")
    return _apply_layout(fig, "Price", height=410)


def cumulative_return_chart(data: pd.DataFrame) -> go.Figure:
    chart_data = data.copy()
    chart_data["cumulative_return_pct"] = chart_data["cumulative_return"] * 100
    fig = go.Figure(
        go.Scatter(
            x=chart_data["date"],
            y=chart_data["cumulative_return_pct"],
            mode="lines",
            name="Cumulative return",
            line=dict(color=COLOR_RETURN, width=2.2),
            fill="tozeroy",
            fillcolor="rgba(45, 212, 191, 0.16)",
        )
    )
    fig.add_hline(y=0, line_color=COLOR_GRID, line_width=1)
    fig.update_layout(title="Cumulative Return")
    return _apply_layout(fig, "Cumulative return (%)", height=410)


def return_distribution_chart(data: pd.DataFrame) -> go.Figure:
    chart_data = data.copy()
    chart_data["daily_return_pct"] = chart_data["daily_return"] * 100
    positive = chart_data[chart_data["daily_return_pct"] >= 0]
    negative = chart_data[chart_data["daily_return_pct"] < 0]

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=negative["daily_return_pct"],
            nbinsx=40,
            name="Negative days",
            marker_color=COLOR_DOWN,
            opacity=0.78,
        )
    )
    fig.add_trace(
        go.Histogram(
            x=positive["daily_return_pct"],
            nbinsx=40,
            name="Positive days",
            marker_color=COLOR_UP,
            opacity=0.78,
        )
    )
    fig.add_vline(x=0, line_color=COLOR_MUTED, line_width=1)
    fig.update_layout(title="Daily Return Distribution", barmode="overlay")
    return _apply_layout(fig, "Trading days", height=335)


def drawdown_chart(data: pd.DataFrame) -> go.Figure:
    chart_data = data.copy()
    chart_data["drawdown_pct"] = chart_data["drawdown"] * 100
    fig = go.Figure(
        go.Scatter(
            x=chart_data["date"],
            y=chart_data["drawdown_pct"],
            mode="lines",
            name="Drawdown",
            line=dict(color=COLOR_DRAWDOWN, width=1.8),
            fill="tozeroy",
            fillcolor="rgba(249, 115, 22, 0.20)",
        )
    )
    fig.update_layout(title="Drawdown from Prior Peak")
    return _apply_layout(fig, "Drawdown (%)", height=335)


def rolling_metrics_chart(data: pd.DataFrame) -> go.Figure:
    chart_data = data.copy()
    chart_data["rolling_volatility_pct"] = chart_data["rolling_volatility"] * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=chart_data["date"],
            y=chart_data["rolling_volatility_pct"],
            mode="lines",
            name="Rolling volatility (%)",
            line=dict(color=COLOR_RISK, width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=chart_data["date"],
            y=chart_data["rolling_sharpe"],
            mode="lines",
            name="Rolling Sharpe Ratio",
            yaxis="y2",
            line=dict(color=COLOR_RETURN, width=2),
        )
    )
    fig.update_layout(
        title="Rolling Risk Metrics",
        template="plotly_dark",
        paper_bgcolor=COLOR_PANEL,
        plot_bgcolor=COLOR_PANEL,
        font=dict(color=COLOR_TEXT, size=12),
        margin=dict(l=22, r=22, t=50, b=46),
        hovermode="x unified",
        xaxis_title=None,
        yaxis=dict(
            title="Rolling volatility (%)",
            gridcolor=COLOR_GRID,
            zeroline=False,
            color=COLOR_MUTED,
        ),
        yaxis2=dict(
            title="Rolling Sharpe Ratio",
            overlaying="y",
            side="right",
            gridcolor=COLOR_GRID,
            zeroline=False,
            color=COLOR_MUTED,
        ),
        xaxis=dict(gridcolor=COLOR_GRID, zeroline=False, color=COLOR_MUTED),
        legend_title_text=None,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        height=335,
    )
    return fig
