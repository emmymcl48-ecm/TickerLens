"""Fetch live financial metrics for a ticker using yfinance."""

from datetime import datetime
import yfinance as yf


def fetch_metrics(ticker: str) -> dict | None:
    """Return a flat dict of current financial metrics, or None if yfinance fails.

    Returns None (not an exception) if Yahoo is unreachable so the caller
    can fall back to a combined Claude call.
    """
    symbol = ticker.upper().strip()

    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        if not info or info.get("quoteType") is None:
            print(f"  yfinance returned no data for {symbol}")
            return None

        return {
            "ticker": symbol,
            "dataSource": "Yahoo Finance",
            "dataDate": datetime.now().strftime("%B %d, %Y"),
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "exchange": info.get("exchange"),
            "currency": info.get("currency", "USD"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "marketCap": info.get("marketCap"),
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "priceToBook": info.get("priceToBook"),
            "enterpriseToEbitda": info.get("enterpriseToEbitda"),
            "enterpriseToRevenue": info.get("enterpriseToRevenue"),
            "grossMargin": info.get("grossMargins"),
            "operatingMargin": info.get("operatingMargins"),
            "netMargin": info.get("profitMargins"),
            "returnOnEquity": info.get("returnOnEquity"),
            "returnOnAssets": info.get("returnOnAssets"),
            "currentRatio": info.get("currentRatio"),
            "quickRatio": info.get("quickRatio"),
            "debtToEquity": info.get("debtToEquity"),
            "beta": info.get("beta"),
            "fiftyDayAvg": info.get("fiftyDayAverage"),
            "twoHundredDayAvg": info.get("twoHundredDayAverage"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "revenueGrowth": info.get("revenueGrowth"),
            "earningsGrowth": info.get("earningsGrowth"),
        }
    except Exception as e:
        print(f"  yfinance failed for {symbol}: {e}")
        return None
