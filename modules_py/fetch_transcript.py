"""Retrieve the latest earnings call transcript summary via Claude web search."""

import json
import re
import anthropic


def fetch_transcript(ticker: str) -> dict | None:
    """Search the web for the latest earnings transcript and return a summary.

    Returns dict with keys: title, quarter, date, text — or None if not found.
    """
    symbol = ticker.upper()
    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=[{
                "role": "user",
                "content": (
                    f"Search the web for the most recent quarterly earnings call for "
                    f"stock ticker {symbol}.\n\n"
                    "After searching, provide:\n"
                    "1. First line must be: QUARTER: <e.g. Q4 2025>\n"
                    "2. Second line must be: DATE: <e.g. February 26, 2026>\n"
                    "3. Third line must be: COMPANY: <full company name>\n\n"
                    "Then provide a detailed summary covering:\n"
                    "- Key financial results (revenue, EPS, year-over-year changes)\n"
                    "- Management's forward guidance and strategy\n"
                    "- Key themes, risks, and opportunities\n"
                    "- Analyst Q&A highlights\n"
                    "- Management's tone (confident, cautious, defensive)\n\n"
                    "If a full transcript isn't available, summarize the earnings "
                    "results and coverage you find. Focus on the MOST RECENT quarter."
                ),
            }],
        )

        # Collect ALL text from the response
        text = _extract_text(response)

        if not text or len(text) < 50:
            return None

        # Parse metadata from the response
        quarter = _extract_field(text, r"QUARTER:\s*(.+)")
        date = _extract_field(text, r"DATE:\s*(.+)")
        company = _extract_field(text, r"COMPANY:\s*(.+)") or symbol

        # Remove the metadata lines from the summary text
        summary = re.sub(
            r"^(QUARTER:|DATE:|COMPANY:|TRANSCRIPT_INFO:).*$",
            "", text, flags=re.MULTILINE,
        ).strip()

        if not summary or len(summary) < 50:
            summary = text  # Just use the full text if stripping removed too much

        return {
            "title": f"{company} ({symbol}) Earnings Call Summary",
            "quarter": quarter,
            "date": date,
            "company": company,
            "text": summary,
        }
    except Exception as e:
        print(f"Transcript fetch error for {symbol}: {e}")
        return None


def _extract_text(response) -> str:
    """Extract all text content from a Claude response, including after tool use."""
    parts = []
    for block in response.content:
        if block.type == "text" and block.text.strip():
            parts.append(block.text.strip())
    return "\n\n".join(parts)


def _extract_field(text: str, pattern: str) -> str | None:
    """Extract a single metadata field from text."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None
