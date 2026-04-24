"""WRDS data access utilities.

The functions in this module require a valid WRDS account. Credentials are
passed at runtime and are not written to disk by this project.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import wrds


def _as_sql_date(value: date | str) -> str:
    """Return a YYYY-MM-DD string for WRDS SQL parameters."""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def connect_to_wrds(username: str, password: str) -> wrds.Connection:
    """Open a WRDS connection using runtime credentials."""
    if not username or not password:
        raise ValueError("WRDS username and password are required.")

    return wrds.Connection(
        wrds_username=username.strip(),
        wrds_password=password,
        verbose=False,
    )


def close_wrds_connection(conn: Any) -> None:
    """Close a WRDS connection if it exposes a close method."""
    if conn is not None and hasattr(conn, "close"):
        conn.close()


COMMON_SHARE_CIZ_FILTER = """
    and sharetype = 'NS'
    and securitytype = 'EQTY'
    and securitysubtype = 'COM'
    and usincflg = 'Y'
    and issuertype in ('ACOR', 'CORP')
    and conditionaltype = 'RW'
    and tradingstatusflg = 'A'
"""


def get_matching_securities(
    conn: wrds.Connection,
    ticker: str,
    start_date: date | str,
    end_date: date | str,
) -> pd.DataFrame:
    """Find common-share CRSP CIZ securities matching a ticker and date range."""
    sql = f"""
        select distinct
            permno,
            ticker,
            min(dlycaldt) as namedt,
            max(dlycaldt) as nameendt,
            primaryexch,
            sharetype,
            securitytype,
            securitysubtype,
            usincflg,
            issuertype,
            count(*) as observations
        from crsp.dsf_v2
        where trim(upper(ticker)) = %(ticker)s
          and dlycaldt between %(start_date)s and %(end_date)s
          {COMMON_SHARE_CIZ_FILTER}
        group by
            permno,
            ticker,
            primaryexch,
            sharetype,
            securitytype,
            securitysubtype,
            usincflg,
            issuertype
        order by observations desc, nameendt desc
    """
    params = {
        "ticker": ticker.strip().upper(),
        "start_date": _as_sql_date(start_date),
        "end_date": _as_sql_date(end_date),
    }
    data = conn.raw_sql(sql, params=params, date_cols=["namedt", "nameendt"])
    if not data.empty:
        data["comnam"] = data["ticker"].str.strip()
    return data.reset_index(drop=True)


def get_ticker_history(conn: wrds.Connection, ticker: str) -> pd.DataFrame:
    """Return available CRSP CIZ records for a ticker for diagnosis."""
    sql = """
        select distinct
            permno,
            ticker,
            min(dlycaldt) as namedt,
            max(dlycaldt) as nameendt,
            primaryexch,
            sharetype,
            securitytype,
            securitysubtype,
            usincflg,
            issuertype,
            count(*) as observations
        from crsp.dsf_v2
        where trim(upper(ticker)) = %(ticker)s
        group by
            permno,
            ticker,
            primaryexch,
            sharetype,
            securitytype,
            securitysubtype,
            usincflg,
            issuertype
        order by nameendt desc, observations desc
    """
    data = conn.raw_sql(
        sql,
        params={"ticker": ticker.strip().upper()},
        date_cols=["namedt", "nameendt"],
    )
    return data.reset_index(drop=True)


def get_latest_crsp_daily_date(conn: wrds.Connection) -> date | None:
    """Return the latest available date in CRSP CIZ daily stock data."""
    sql = "select max(dlycaldt) as latest_date from crsp.dsf_v2"
    data = conn.raw_sql(sql, date_cols=["latest_date"], chunksize=None)
    if data.empty or pd.isna(data.loc[0, "latest_date"]):
        return None
    return pd.Timestamp(data.loc[0, "latest_date"]).date()


def fetch_daily_stock_data(
    conn: wrds.Connection,
    permno: int,
    start_date: date | str,
    end_date: date | str,
) -> pd.DataFrame:
    """Download daily CRSP CIZ stock data for one PERMNO."""
    sql = f"""
        select
            dlycaldt as date,
            permno,
            dlyprc as price,
            dlyret as daily_return,
            dlyvol as volume,
            shrout as shares_outstanding,
            dlycap as market_cap
        from crsp.dsf_v2
        where permno = %(permno)s
          and dlycaldt between %(start_date)s and %(end_date)s
          {COMMON_SHARE_CIZ_FILTER}
        order by dlycaldt
    """
    params = {
        "permno": int(permno),
        "start_date": _as_sql_date(start_date),
        "end_date": _as_sql_date(end_date),
    }
    data = conn.raw_sql(sql, params=params, date_cols=["date"])

    if data.empty:
        return data

    data["price"] = pd.to_numeric(data["price"], errors="coerce").abs()
    data["daily_return"] = pd.to_numeric(data["daily_return"], errors="coerce")
    data["volume"] = pd.to_numeric(data["volume"], errors="coerce")
    data["shares_outstanding"] = pd.to_numeric(data["shares_outstanding"], errors="coerce")
    data["market_cap_millions"] = pd.to_numeric(data["market_cap"], errors="coerce")
    return data.reset_index(drop=True)
