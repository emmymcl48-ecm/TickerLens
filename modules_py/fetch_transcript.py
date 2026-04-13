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
            max_tokens=3500,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=[{
                "role": "user",
                "content": (
                    f"Search the web for the most recent quarterly earnings call transcript "
                    f"for stock ticker {symbol}. Try searching for:\n"
                    f'- "{symbol} earnings call transcript 2026"\n'
                    f'- "{symbol} earnings call transcript 2025"\n'
                    f'- "{symbol} quarterly results transcript"\n\n'
                    "Look on Motley Fool, Seeking Alpha, The Street, or any financial news source.\n\n"
                    "Once you find the most recent transcript or earnings call coverage, respond with "
                    "EXACTLY this format — a JSON header line followed by your summary:\n\n"
                    "TRANSCRIPT_INFO: {\"quarter\": \"Q4 2025\", \"date\": \"February 26, 2026\", "
                    "\"company\": \"Full Company Name\"}\n\n"
                    "Then provide a detailed summary (at least 600 words) that includes:\n"
                    "1. Key financial results discussed (revenue, EPS, year-over-year changes)\n"
                    "2. Management's forward guidance and strategy comments\n"
                    "3. Key themes, risks, and opportunities mentioned\n"
                    "4. Analyst Q&A highlights — what were analysts most focused on?\n"
                    "5. Management's tone — confident, cautious, defensive?\n\n"
                    "If you find earnings results coverage but not a full transcript, that is fine — "
                    "summarize whatever earnings information you can find. The important thing is to "
                    "find the MOST RECENT quarter's earnings information."
                ),
            }],
        )

        text_blocks = [b.text for b in response.content if b.type == "text"]
        text = "\n\n".join(text_blocks)

        if not text or len(text) < 100:
            return None

        # Parse the TRANSCRIPT_INFO header if present
        quarter = None
        date = None
        company = symbol

        info_match = re.search(r'TRANSCRIPT_INFO:\s*(\{[^}]+\})', text)
        if info_match:
            try:
                info = json.loads(info_match.group(1))
                quarter = info.get("quarter")
                date = info.get("date")
                company = info.get("company", symbol)
            except json.JSONDecodeError:
                pass
            # Remove the header line from the summary text
            text = text[info_match.end():].strip()

        if not text or len(text) < 100:
            return None

        return {
            "title": f"{company} ({symbol}) Earnings Call Summary",
            "quarter": quarter,
            "date": date,
            "company": company,
            "text": text,
        }
    except Exception as e:
        print(f"Transcript fetch error for {symbol}: {e}")
        return None
