"""Retrieve the latest earnings call transcript summary via Claude web search."""

import anthropic


def fetch_transcript(ticker: str) -> dict | None:
    """Search the web for the latest earnings transcript and return a summary."""
    symbol = ticker.upper()
    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
            messages=[{
                "role": "user",
                "content": (
                    f"Find the most recent quarterly earnings call transcript for {symbol}. "
                    "Search for it on Motley Fool, Seeking Alpha, or any reliable financial source.\n\n"
                    "Once you find it, provide a detailed summary (at least 800 words) that includes:\n"
                    "1. The quarter and date of the call\n"
                    "2. Key financial results discussed (revenue, EPS, guidance)\n"
                    "3. Direct quotes from management about forward guidance and strategy\n"
                    "4. Key themes, risks, and opportunities mentioned\n"
                    "5. Analyst Q&A highlights\n"
                    "6. Management's tone — confident, cautious, defensive?\n\n"
                    "Format your response as plain text starting with the company name and quarter."
                ),
            }],
        )

        text_blocks = [b.text for b in response.content if b.type == "text"]
        text = "\n\n".join(text_blocks)

        if not text or len(text) < 200:
            return None

        return {"title": f"{symbol} Latest Earnings Call Summary", "text": text}
    except Exception as e:
        print(f"Transcript fetch error for {symbol}: {e}")
        return None
