"""Fetch live financial metrics for a ticker using yfinance, with Claude fallback."""

import yfinance as yf


def fetch_metrics(ticker: str) -> dict:
    """Return a flat dict of financial metrics for the given ticker.

    Tries yfinance first. If Yahoo blocks the request (common on cloud IPs),
    falls back to Claude with web search.
    """
    symbol = ticker.upper().strip()

    try:
        result = _fetch_via_yfinance(symbol)
        if result:
            return result
    except Exception as e:
        print(f"  yfinance failed ({e}), falling back to Claude web search...")

    # Fallback: Claude with web search
    return _fetch_via_claude(symbol)


def _fetch_via_yfinance(symbol: str) -> dict | None:
    """Attempt to fetch metrics via yfinance."""
    stock = yf.Ticker(symbol)
    info = stock.info

    if not info or info.get("quoteType") is None:
        return None

    return _build_result(info, symbol)


def _fetch_via_claude(symbol: str) -> dict:
    """Fallback: use Claude with web search to get financial metrics."""
    import json
    import re
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{
            "role": "user",
            "content": (
                f"Look up the current live financial data for stock ticker {symbol} "
                "from Yahoo Finance or another reliable source. Search the web to get "
                "the most up-to-date numbers.\n\n"
                "Return ONLY a JSON object with these exact fields (use null for unavailable data):\n"
                "{\n"
                '  "name": "Full Company Name",\n'
                '  "sector": "sector name",\n'
                '  "industry": "specific industry",\n'
                '  "currentPrice": current stock price as number,\n'
                '  "marketCap": market cap in dollars as number,\n'
                '  "trailingPE": trailing P/E ratio,\n'
                '  "forwardPE": forward P/E ratio,\n'
                '  "priceToBook": price-to-book ratio,\n'
                '  "enterpriseToEbitda": EV/EBITDA ratio,\n'
                '  "enterpriseToRevenue": EV/Revenue ratio,\n'
                '  "grossMargin": as decimal (e.g. 0.45 for 45%),\n'
                '  "operatingMargin": as decimal,\n'
                '  "netMargin": as decimal,\n'
                '  "returnOnEquity": as decimal,\n'
                '  "returnOnAssets": as decimal,\n'
                '  "currentRatio": current ratio,\n'
                '  "quickRatio": quick ratio,\n'
                '  "debtToEquity": debt-to-equity as percentage (e.g. 150 for 150%),\n'
                '  "beta": beta coefficient,\n'
                '  "fiftyDayAvg": 50-day moving average price,\n'
                '  "twoHundredDayAvg": 200-day moving average price,\n'
                '  "fiftyTwoWeekHigh": 52-week high price,\n'
                '  "fiftyTwoWeekLow": 52-week low price,\n'
                '  "revenueGrowth": YoY revenue growth as decimal,\n'
                '  "earningsGrowth": YoY earnings growth as decimal\n'
                "}\n\n"
                "IMPORTANT: Return ONLY the JSON. No explanations, no markdown code blocks."
            ),
        }],
    )

    text_blocks = [b.text for b in response.content if b.type == "text"]
    text = "".join(text_blocks)
    json_match = re.search(r"\{[\s\S]*\}", text)

    if not json_match:
        raise ValueError(f"Could not retrieve financial data for {symbol}. The ticker may be invalid.")

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
