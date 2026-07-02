from __future__ import annotations

from typing import Any

import pandas as pd
from fastmcp import FastMCP
from langchain.tools import tool
from yfinance import Ticker
from utils.cache import redis_cache
from schema.schemas import (
    BalanceSheetSummary,
    CompanyInfoToolResponse,
    FinancialsToolResponse,
    IncomeStatementSummary,
    OHLCVToolResponse,
    StockPriceToolResponse,
)

mcp = FastMCP("Yahoo Finance")

_VALID_PERIODS = {
    "1d",
    "5d",
    "1mo",
    "3mo",
    "6mo",
    "1y",
    "2y",
    "5y",
    "10y",
    "ytd",
    "max",
}


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized:
        raise ValueError("INVALID_TICKER: ticker cannot be empty")
    return normalized


def _validate_period(period: str) -> str:
    normalized = period.strip().lower()
    if normalized not in _VALID_PERIODS:
        raise ValueError(
            f"INVALID_PERIOD: supported periods are {sorted(_VALID_PERIODS)}"
        )
    return normalized


def _latest_column(frame: pd.DataFrame) -> Any | None:
    if frame.empty or not len(frame.columns):
        return None
    return max(frame.columns)


def _statement_value(
    frame: pd.DataFrame, column: Any, aliases: tuple[str, ...]
) -> float | None:
    if frame.empty or column is None:
        return None

    normalized_lookup = {
        str(index).replace(" ", "").replace("_", "").lower(): index
        for index in frame.index
    }

    for alias in aliases:
        index = normalized_lookup.get(alias.replace(" ", "").replace("_", "").lower())
        if index is None:
            continue

        value = frame.at[index, column]
        if pd.isna(value):
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return None

@redis_cache(ttl_seconds=300)
def _get_stock_price_impl(ticker: str) -> StockPriceToolResponse:
    """Return the latest stock price and day-over-day percentage change."""
    normalized_ticker = _normalize_ticker(ticker)
    tick = Ticker(normalized_ticker)
    
    # Try to calculate 52-week high and low from 1y history
    try:
        hist = tick.history(period="1y", auto_adjust=False)
    except Exception:
        hist = pd.DataFrame()

    fifty_two_week_high = None
    fifty_two_week_low = None
    
    if not hist.empty:
        # Calculate from 1-year history
        if "High" in hist.columns and not hist["High"].empty:
            fifty_two_week_high = float(hist["High"].max())
        if "Low" in hist.columns and not hist["Low"].empty:
            fifty_two_week_low = float(hist["Low"].min())
            
        # Get last price and previous close from history if possible
        if "Close" in hist.columns and not hist["Close"].empty:
            last_price = float(hist["Close"].iloc[-1])
            previous_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last_price
            percentage_change = (
                ((last_price - previous_close) / previous_close) * 100
                if previous_close
                else 0.0
            )
        else:
            # Fallback to info
            info = getattr(tick, "info", None) or tick.get_info()
            last_price = float(info.get("lastPrice") or info.get("currentPrice") or 0.0)
            previous_close = float(info.get("previousClose") or 0.0)
            percentage_change = (
                ((last_price - previous_close) / previous_close) * 100
                if previous_close
                else 0.0
            )
    else:
        # Full fallback to info if history is completely empty
        info = getattr(tick, "info", None) or tick.get_info()
        last_price = float(info.get("lastPrice") or info.get("currentPrice") or 0.0)
        previous_close = float(info.get("previousClose") or 0.0)
        percentage_change = (
            ((last_price - previous_close) / previous_close) * 100
            if previous_close
            else 0.0
        )
        # Try info fallback for 52-week high/low
        fifty_two_week_high = info.get("fiftyTwoWeekHigh")
        fifty_two_week_low = info.get("fiftyTwoWeekLow")
        if fifty_two_week_high is not None:
            fifty_two_week_high = float(fifty_two_week_high)
        if fifty_two_week_low is not None:
            fifty_two_week_low = float(fifty_two_week_low)

    # Get currency
    currency = "USD"
    try:
        info = getattr(tick, "info", None) or tick.get_info()
        currency = info.get("currency", "USD")
    except Exception:
        pass

    return StockPriceToolResponse(
        ticker=normalized_ticker,
        current_price=last_price,
        percentage_change=percentage_change,
        currency=currency,
        fifty_two_week_high=fifty_two_week_high,
        fifty_two_week_low=fifty_two_week_low,
    )



@tool
def get_stock_price_tool(ticker: str) -> StockPriceToolResponse:
    """Retrieve the latest stock price and day-over-day percentage change.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        StockPriceToolResponse with current price and percentage change
    """
    return _get_stock_price_impl(ticker)


@mcp.tool
def get_stock_price(ticker: str) -> StockPriceToolResponse:
    """Retrieve the latest stock price and day-over-day percentage change.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        StockPriceToolResponse with current price and percentage change
    """
    return _get_stock_price_impl(ticker)


# Maximum number of OHLCV bars returned to stay within LLM token budgets.
_MAX_OHLCV_BARS = 10

@redis_cache(ttl_seconds=300)
def _get_ohlcv_impl(ticker: str, period: str) -> OHLCVToolResponse:
    """Return the most recent OHLCV bars (up to _MAX_OHLCV_BARS) for the
    requested ticker and period.  Capping the rows prevents 413 token-limit
    errors when the response is serialised into the LLM context window."""
    normalized_ticker = _normalize_ticker(ticker)
    normalized_period = _validate_period(period)
    tick = Ticker(normalized_ticker)
    ohlcv_data = tick.history(period=normalized_period, auto_adjust=False)

    # Keep only the most-recent rows to limit payload size.
    ohlcv_data = ohlcv_data.tail(_MAX_OHLCV_BARS)

    records = []
    for timestamp, row in ohlcv_data.iterrows():
        records.append(
            {
                "date": timestamp.to_pydatetime()
                if hasattr(timestamp, "to_pydatetime")
                else timestamp,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            }
        )

    return OHLCVToolResponse(ticker=normalized_ticker, period=normalized_period, data=records)


@tool
def get_ohlcv_tool(ticker: str, period: str) -> OHLCVToolResponse:
    """Retrieve OHLCV (Open, High, Low, Close, Volume) bars for a stock.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        period: Time period for data ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        
    Returns:
        OHLCVToolResponse with historical price and volume data
    """
    return _get_ohlcv_impl(ticker, period)


@mcp.tool
def get_ohlcv(ticker: str, period: str) -> OHLCVToolResponse:
    """Retrieve OHLCV (Open, High, Low, Close, Volume) bars for a stock.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        period: Time period for data ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        
    Returns:
        OHLCVToolResponse with historical price and volume data
    """
    return _get_ohlcv_impl(ticker, period)

@redis_cache(ttl_seconds=300)
def _get_company_info_impl(ticker: str) -> CompanyInfoToolResponse:
    """Return company profile data for the requested ticker."""
    normalized_ticker = _normalize_ticker(ticker)
    tick = Ticker(normalized_ticker)
    data = tick.get_info()
    return CompanyInfoToolResponse(
        ticker=normalized_ticker,
        name=data.get("longName"),
        description=data.get("longBusinessSummary"),
        sector=data.get("sector"),
        industry=data.get("industry"),
        market_cap=data.get("marketCap"),
    )


@tool
def get_company_info_tool(ticker: str) -> CompanyInfoToolResponse:
    """Retrieve company profile and information.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        CompanyInfoToolResponse with company name, description, sector, and industry
    """
    return _get_company_info_impl(ticker)


@mcp.tool
def get_company_info(ticker: str) -> CompanyInfoToolResponse:
    """Retrieve company profile and information.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        CompanyInfoToolResponse with company name, description, sector, and industry
    """
    return _get_company_info_impl(ticker)

@redis_cache(ttl_seconds=300)
def _get_financials_impl(ticker: str) -> FinancialsToolResponse:
    normalized_ticker = _normalize_ticker(ticker)
    stock = Ticker(normalized_ticker)

    try:
        income_statement = stock.get_income_stmt(freq="yearly")
        balance_sheet = stock.get_balance_sheet(freq="yearly")
    except Exception as exc:  # pragma: no cover - provider-specific failure path
        raise RuntimeError(
            f"PROVIDER_ERROR: failed to load financial statements: {exc}"
        ) from exc

    if income_statement.empty and balance_sheet.empty:
        raise ValueError("DATA_NOT_FOUND: no yearly financial statements available")

    income_column = _latest_column(income_statement)
    balance_column = _latest_column(balance_sheet)

    fiscal_year = None
    latest_column = income_column or balance_column
    if latest_column is not None:
        year = getattr(latest_column, "year", None)
        fiscal_year = int(year) if year is not None else None

    currency = None
    try:
        currency = stock.get_info().get("financialCurrency") or stock.get_info().get("currency")
    except Exception:
        currency = None

    income_summary = IncomeStatementSummary(
        total_revenue=_statement_value(
            income_statement,
            income_column,
            ("Total Revenue", "Operating Revenue"),
        ),
        gross_profit=_statement_value(income_statement, income_column, ("Gross Profit",)),
        operating_income=_statement_value(
            income_statement,
            income_column,
            ("Operating Income",),
        ),
        net_income=_statement_value(
            income_statement,
            income_column,
            ("Net Income", "Net Income Common Stockholders"),
        ),
        diluted_eps=_statement_value(
            income_statement,
            income_column,
            ("Diluted EPS",),
        ),
    )

    balance_summary = BalanceSheetSummary(
        total_assets=_statement_value(balance_sheet, balance_column, ("Total Assets",)),
        total_liabilities=_statement_value(
            balance_sheet,
            balance_column,
            ("Total Liabilities Net Minority Interest", "Total Liabilities"),
        ),
        total_equity=_statement_value(
            balance_sheet,
            balance_column,
            ("Stockholders Equity", "Total Equity Gross Minority Interest"),
        ),
        cash_and_cash_equivalents=_statement_value(
            balance_sheet,
            balance_column,
            (
                "Cash Cash Equivalents And Short Term Investments",
                "Cash And Cash Equivalents",
                "Cash",
            ),
        ),
        total_debt=_statement_value(balance_sheet, balance_column, ("Total Debt",)),
    )

    return FinancialsToolResponse(
        ticker=normalized_ticker,
        currency=currency,
        fiscal_year=fiscal_year,
        income_statement=income_summary,
        balance_sheet=balance_summary,
    )


@tool
def get_financials_tool(ticker: str) -> FinancialsToolResponse:
    """Retrieve financial statements including income statement and balance sheet.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        FinancialsToolResponse with income statement and balance sheet summaries
    """
    return _get_financials_impl(ticker)


@mcp.tool
def get_financials(ticker: str) -> FinancialsToolResponse:
    """Retrieve financial statements including income statement and balance sheet.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        FinancialsToolResponse with income statement and balance sheet summaries
    """
    return _get_financials_impl(ticker)


def build_langchain_tools() -> list[Any]:
    return [get_stock_price_tool, get_ohlcv_tool, get_company_info_tool, get_financials_tool]


if __name__ == "__main__":
    mcp.run(transport="stdio")
