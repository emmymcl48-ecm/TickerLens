"""Fetch live financial metrics for a ticker using yfinance, with Claude fallback."""

import yfinance as yf


def fetch_metrics(ticker: str) -> dict:
    """Return a flat dict of financial metrics for the given ticker.

    Tries yfinance first. If Yahoo blocks the request (common on cloud IPs),
    falls back to Claude (no web search — uses training knowledge to avoid
    burning rate limit, since earnings sentiment needs web search).
    """
    symbol = ticker.upper().strip()

    try:
        result = _fetch_via_yfinance(symbol)
        if result:
            return result
    except Exception as e:
        print(f"  yfinance failed ({e}), falling back to Claude...")

    return _fetch_via_claude(symbol)


def _fetch_via_yfinance(symbol: str) -> dict | None:
    """Attempt to fetch metrics via yfinance."""
    stock = yf.Ticker(symbol)
    info = stock.info

    if not info or info.get("quoteType") is None:
        return None

    return _build_result(info, symbol)


def _fetch_via_claude(symbol: str) -> dict:
    """Fallback: use Claude WITHOUT web search to get financial metrics.

    Does not use web search to avoid consuming rate limit — the earnings
    sentiment module needs that budget. Claude's training data includes
    recent financial metrics for publicly traded companies.
    """
    import json
    import re
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": (
                f"Provide the most recent financial data you know for stock ticker {symbol}. "
                "Return ONLY a JSON object with these fields (null if unknown):\n"
                '{"name":"Company Name","sector":"sector","industry":"industry",'
                '"currentPrice":0,"marketCap":0,"trailingPE":0,"forwardPE":0,'
                '"priceToBook":0,"enterpriseToEbitda":0,"enterpriseToRevenue":0,'
                '"grossMargin":0.0,"operatingMargin":0.0,"netMargin":0.0,'
                '"returnOnEquity":0.0,"returnOnAssets":0.0,'
                '"currentRatio":0,"quickRatio":0,"debtToEquity":0,"beta":0,'
                '"fiftyDayAvg":0,"twoHundredDayAvg":0,'
                '"fiftyTwoWeekHigh":0,"fiftyTwoWeekLow":0,'
                '"revenueGrowth":0.0,"earningsGrowth":0.0}\n'
                "Return ONLY JSON, no other text."
            ),
        }],
    )

    text = response.content[0].text.strip()
    json_match = re.search(r"\{[\s\S]*\}", text)

    if not json_match:
        raise ValueError(f'Ticker "{symbol}" not found. Check the symbol and try again.')

    d = json.loads(json_match.group())
    return {
        "ticker": symbol,
        "name": d.get("name") or symbol,
        "sector": d.get("sector"),
        "industry": d.get("industry"),
        "exchange": None,
        "currency": "USD",
        "currentPrice": d.get("currentPrice"),
        "marketCap": d.get("marketCap"),
        "trailingPE": d.get("trailingPE"),
        "forwardPE": d.get("forwardPE"),
        "priceToBook": d.get("priceToBook"),
        "enterpriseToEbitda": d.get("enterpriseToEbitda"),
        "enterpriseToRevenue": d.get("enterpriseToRevenue"),
        "grossMargin": d.get("grossMargin"),
        "operatingMargin": d.get("operatingMargin"),
        "netMargin": d.get("netMargin"),
        "returnOnEquity": d.get("returnOnEquity"),
        "returnOnAssets": d.get("returnOnAssets"),
        "currentRatio": d.get("currentRatio"),
        "quickRatio": d.get("quickRatio"),
        "debtToEquity": d.get("debtToEquity"),
        "beta": d.get("beta"),
        "fiftyDayAvg": d.get("fiftyDayAvg"),
        "twoHundredDayAvg": d.get("twoHundredDayAvg"),
        "fiftyTwoWeekHigh": d.get("fiftyTwoWeekHigh"),
        "fiftyTwoWeekLow": d.get("fiftyTwoWeekLow"),
        "revenueGrowth": d.get("revenueGrowth"),
        "earningsGrowth": d.get("earningsGrowth"),
    }


def _build_result(info: dict, symbol: str) -> dict:
    return {
        "ticker": symbol,
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
