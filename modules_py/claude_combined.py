"""Combined Claude web search: fetch current metrics + earnings sentiment in ONE call.

Used when yfinance is unavailable (cloud IP blocked). A single call avoids
rate limiting that would occur with two separate web search requests.
"""

import json
import re
import time
from datetime import datetime
import anthropic


def fetch_metrics_and_sentiment(ticker: str) -> tuple[dict, dict]:
    """Return (metrics_dict, sentiment_pillar) from a single Claude web search call.

    Always returns both — metrics may have some null fields, sentiment always
    has a score/signal/reasoning.
    """
    symbol = ticker.upper()
    client = anthropic.Anthropic()

    try:
        return _combined_call(symbol, client)
    except anthropic.RateLimitError:
        print(f"  Rate limited, retrying in 15s...")
        time.sleep(15)
        try:
            return _combined_call(symbol, client)
        except Exception as e:
            return _fallback(symbol, str(e))
    except Exception as e:
        return _fallback(symbol, str(e))


def _combined_call(symbol: str, client: anthropic.Anthropic) -> tuple[dict, dict]:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{
            "role": "user",
            "content": (
                f"I need two things for stock ticker {symbol}. Search the web for current data.\n\n"
                "1. CURRENT financial metrics from today\n"
                f"2. Most recent earnings call analysis — search the company's investor relations "
                f"page first (e.g. {symbol} investor relations earnings), then Motley Fool, "
                "Seeking Alpha, or other sources\n\n"
                "Respond with ONLY this JSON (no other text):\n"
                "{\n"
                '  "metrics": {\n'
                '    "name": "Company Name",\n'
                '    "sector": "sector",\n'
                '    "industry": "industry",\n'
                '    "currentPrice": 0,\n'
                '    "marketCap": 0,  // raw dollars, e.g. 3500000000000 for $3.5 trillion\n'
                '    "trailingPE": 0,\n'
                '    "forwardPE": 0,\n'
                '    "priceToBook": 0,\n'
                '    "enterpriseToEbitda": 0,\n'
                '    "enterpriseToRevenue": 0,\n'
                '    "grossMargin": 0.0,\n'
                '    "operatingMargin": 0.0,\n'
                '    "netMargin": 0.0,\n'
                '    "returnOnEquity": 0.0,\n'
                '    "returnOnAssets": 0.0,\n'
                '    "currentRatio": 0,\n'
                '    "quickRatio": 0,\n'
                '    "debtToEquity": 0,\n'
                '    "beta": 0,\n'
                '    "fiftyDayAvg": 0,\n'
                '    "twoHundredDayAvg": 0,\n'
                '    "fiftyTwoWeekHigh": 0,\n'
                '    "fiftyTwoWeekLow": 0,\n'
                '    "revenueGrowth": 0.0,\n'
                '    "earningsGrowth": 0.0,\n'
                '    "source": "e.g. Yahoo Finance, Google Finance, MarketWatch"\n'
                '  },\n'
                '  "sentiment": {\n'
                '    "quarter": "Q4 2025",\n'
                '    "date": "January 29, 2026",\n'
                '    "score": 7,\n'
                '    "signal": "Green",\n'
                '    "reasoning": "2-3 sentence objective analysis of earnings call"\n'
                '  }\n'
                "}\n\n"
                "Rules:\n"
                "- metrics: Use current/today's data. Margins as decimals (0.45 = 45%). "
                "debtToEquity as percentage (150 = 150%). Use null for unknown fields.\n"
                "- sentiment.score: 1-10 (1=bearish, 10=bullish). "
                "Green >= 6.5, Yellow 4-6.5, Red < 4.\n"
                "- sentiment.reasoning: Be objective. Focus on management's actual statements, "
                "guidance, and tone.\n"
                "- Return ONLY the JSON."
            ),
        }],
    )

    text_parts = [b.text.strip() for b in response.content if b.type == "text" and b.text.strip()]
    text = "\n".join(text_parts)

    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError(f"Could not parse response for {symbol}")

    parsed = json.loads(json_match.group())

    # Build metrics dict
    m = parsed.get("metrics", {})

    # Normalize marketCap — Claude sometimes returns in billions (e.g. 3500)
    # instead of raw dollars (3500000000000). Any publicly traded company
    # has a market cap > $1M, so a value below that is almost certainly
    # in a compressed unit.
    raw_mcap = m.get("marketCap")
    if raw_mcap and raw_mcap > 0:
        if raw_mcap < 1_000:
            raw_mcap = int(raw_mcap * 1e9)   # was in billions
        elif raw_mcap < 1_000_000:
            raw_mcap = int(raw_mcap * 1e6)   # was in millions

    metrics = {
        "ticker": symbol,
        "dataSource": m.get("source") or "Claude Web Search",
        "dataDate": datetime.now().strftime("%B %d, %Y"),
        "name": m.get("name") or symbol,
        "sector": m.get("sector"),
        "industry": m.get("industry"),
        "exchange": None,
        "currency": "USD",
        "currentPrice": m.get("currentPrice"),
        "marketCap": raw_mcap,
        "trailingPE": m.get("trailingPE"),
        "forwardPE": m.get("forwardPE"),
        "priceToBook": m.get("priceToBook"),
        "enterpriseToEbitda": m.get("enterpriseToEbitda"),
        "enterpriseToRevenue": m.get("enterpriseToRevenue"),
        "grossMargin": m.get("grossMargin"),
        "operatingMargin": m.get("operatingMargin"),
        "netMargin": m.get("netMargin"),
        "returnOnEquity": m.get("returnOnEquity"),
        "returnOnAssets": m.get("returnOnAssets"),
        "currentRatio": m.get("currentRatio"),
        "quickRatio": m.get("quickRatio"),
        "debtToEquity": m.get("debtToEquity"),
        "beta": m.get("beta"),
        "fiftyDayAvg": m.get("fiftyDayAvg"),
        "twoHundredDayAvg": m.get("twoHundredDayAvg"),
        "fiftyTwoWeekHigh": m.get("fiftyTwoWeekHigh"),
        "fiftyTwoWeekLow": m.get("fiftyTwoWeekLow"),
        "revenueGrowth": m.get("revenueGrowth"),
        "earningsGrowth": m.get("earningsGrowth"),
    }

    # Build sentiment pillar
    s = parsed.get("sentiment", {})
    score = max(1.0, min(10.0, float(s.get("score", 5))))
    signal = s.get("signal", "Yellow")
    if signal not in ("Green", "Yellow", "Red"):
        signal = "Green" if score >= 6.5 else ("Yellow" if score >= 4.0 else "Red")
    reasoning = s.get("reasoning", "Analysis complete.")

    quarter = s.get("quarter", "").strip()
    date = s.get("date", "").strip()
    if quarter:
        label = f"[{quarter}"
        if date:
            label += f" — {date}"
        label += "] "
        reasoning = label + reasoning

    sentiment = {
        "name": "Earnings Sentiment",
        "score": round(score, 1),
        "signal": signal,
        "reasoning": reasoning,
    }

    return metrics, sentiment


def _fallback(symbol: str, error: str) -> tuple[dict, dict]:
    """Return empty metrics and neutral sentiment when everything fails."""
    metrics = {
        "ticker": symbol, "dataSource": "N/A", "dataDate": "N/A",
        "name": symbol, "sector": None, "industry": None,
        "exchange": None, "currency": "USD", "currentPrice": None, "marketCap": None,
        "trailingPE": None, "forwardPE": None, "priceToBook": None,
        "enterpriseToEbitda": None, "enterpriseToRevenue": None,
        "grossMargin": None, "operatingMargin": None, "netMargin": None,
        "returnOnEquity": None, "returnOnAssets": None,
        "currentRatio": None, "quickRatio": None, "debtToEquity": None, "beta": None,
        "fiftyDayAvg": None, "twoHundredDayAvg": None,
        "fiftyTwoWeekHigh": None, "fiftyTwoWeekLow": None,
        "revenueGrowth": None, "earningsGrowth": None,
    }
    sentiment = {
        "name": "Earnings Sentiment",
        "score": 5.0,
        "signal": "Yellow",
        "reasoning": f"Analysis unavailable: {error}",
    }
    return metrics, sentiment
