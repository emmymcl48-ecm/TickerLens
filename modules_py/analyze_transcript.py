"""Analyze an earnings call transcript for sentiment using Claude."""

import json
import anthropic


def analyze_transcript(ticker: str, transcript_text: str | None) -> dict:
    """Return a sentiment pillar dict with score, signal, and reasoning."""
    if not transcript_text:
        return {
            "name": "Earnings Sentiment",
            "score": 5.0,
            "signal": "Yellow",
            "reasoning": "No earnings transcript available for analysis.",
        }

    client = anthropic.Anthropic()
    prompt = (
        f"You are a financial analyst evaluating the most recent earnings call transcript for {ticker}.\n\n"
        "Analyze the transcript below and provide:\n"
        "1. A sentiment score from 1-10 (1 = very bearish, 5 = neutral, 10 = very bullish)\n"
        "2. A signal: \"Green\" (bullish, score >= 6.5), \"Yellow\" (neutral, 4-6.5), or \"Red\" (bearish, score < 4)\n"
        "3. A brief 2-3 sentence reasoning covering: management tone, forward guidance, key risks or catalysts\n\n"
        "IMPORTANT: Be objective and non-biased. Focus on what management actually said, not market sentiment. Look for:\n"
        "- Revenue/earnings guidance (raised, maintained, lowered?)\n"
        "- Management confidence vs hedging language\n"
        "- Key growth drivers or headwinds mentioned\n"
        "- Any surprises or changes in strategy\n\n"
        'Respond in exactly this JSON format:\n'
        '{"score": <number>, "signal": "<Green|Yellow|Red>", "reasoning": "<your 2-3 sentence analysis>"}\n\n'
        f"TRANSCRIPT:\n{transcript_text}"
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        import re
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "name": "Earnings Sentiment",
                "score": max(1, min(10, parsed.get("score", 5))),
                "signal": parsed.get("signal", "Yellow") if parsed.get("signal") in ("Green", "Yellow", "Red") else "Yellow",
                "reasoning": parsed.get("reasoning", "Analysis complete."),
            }

        return {
            "name": "Earnings Sentiment",
            "score": 5.0,
            "signal": "Yellow",
            "reasoning": text[:200],
        }
    except Exception as e:
        return {
            "name": "Earnings Sentiment",
            "score": 5.0,
            "signal": "Yellow",
            "reasoning": f"Transcript analysis unavailable: {e}",
        }
