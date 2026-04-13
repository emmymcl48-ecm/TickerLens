"""Single-step earnings sentiment: search for latest earnings AND analyze in one Claude call."""

import json
import re
import anthropic


def get_earnings_sentiment(ticker: str) -> dict:
    """Search the web for the latest earnings call and return a scored sentiment pillar.

    Combines transcript fetching + sentiment analysis into one Claude call.
    Returns a pillar dict with: name, score, signal, reasoning.
    Always returns a result (never None) — defaults to neutral if search fails.
    """
    symbol = ticker.upper()
    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=[{
                "role": "user",
                "content": (
                    f"Search the web for the most recent quarterly earnings call or earnings "
                    f"results for stock ticker {symbol}. Search for things like "
                    f'"{symbol} earnings results", "{symbol} earnings call", '
                    f'"{symbol} quarterly results 2026", "{symbol} quarterly results 2025".\n\n'
                    "After finding the earnings information, analyze it as a financial analyst "
                    "and respond with ONLY this JSON (no other text):\n\n"
                    "{\n"
                    '  "quarter": "Q4 2025",\n'
                    '  "date": "January 29, 2026",\n'
                    '  "score": 7,\n'
                    '  "signal": "Green",\n'
                    '  "reasoning": "Your 2-3 sentence analysis here."\n'
                    "}\n\n"
                    "Rules for your analysis:\n"
                    "- score: 1-10 (1=very bearish, 5=neutral, 10=very bullish)\n"
                    "- signal: Green (score >= 6.5), Yellow (4 to 6.5), Red (< 4)\n"
                    "- reasoning: Cover management tone, forward guidance, and key risks/catalysts. "
                    "Start with the most important takeaway.\n"
                    "- quarter: The fiscal quarter reported (e.g. Q4 2025, Q1 2026)\n"
                    "- date: The date of the earnings call\n"
                    "- Be OBJECTIVE. Focus on what management said, not market reaction.\n\n"
                    "IMPORTANT: Respond with ONLY the JSON object. No markdown, no explanation."
                ),
            }],
        )

        # Extract text from response
        text_parts = [b.text.strip() for b in response.content if b.type == "text" and b.text.strip()]
        text = "\n".join(text_parts)

        if not text:
            return _default_result("Claude returned no text after web search.")

        # Parse JSON from response
        json_match = re.search(r"\{[\s\S]*\}", text)
        if not json_match:
            return _default_result("Could not parse earnings analysis response.")

        parsed = json.loads(json_match.group())

        score = max(1.0, min(10.0, float(parsed.get("score", 5))))
        signal = parsed.get("signal", "Yellow")
        if signal not in ("Green", "Yellow", "Red"):
            signal = "Green" if score >= 6.5 else ("Yellow" if score >= 4.0 else "Red")

        reasoning = parsed.get("reasoning", "Analysis complete.")

        # Prepend quarter info
        quarter = parsed.get("quarter", "").strip()
        date = parsed.get("date", "").strip()
        if quarter:
            label = f"[{quarter}"
            if date:
                label += f" — {date}"
            label += "] "
            reasoning = label + reasoning

        return {
            "name": "Earnings Sentiment",
            "score": round(score, 1),
            "signal": signal,
            "reasoning": reasoning,
        }

    except anthropic.RateLimitError as e:
        return _default_result(f"Rate limited — please try again in a moment.")
    except anthropic.AuthenticationError as e:
        return _default_result(f"API key error — check ANTHROPIC_API_KEY.")
    except Exception as e:
        return _default_result(f"Earnings analysis error: {type(e).__name__}: {e}")


def _default_result(reason: str) -> dict:
    """Return a neutral sentiment result with an explanation."""
    return {
        "name": "Earnings Sentiment",
        "score": 5.0,
        "signal": "Yellow",
        "reasoning": reason,
    }
