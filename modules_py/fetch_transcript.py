"""Retrieve the latest earnings call transcript via direct scraping + Claude fallback."""

import json
import re
import anthropic
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_transcript(ticker: str) -> dict | None:
    """Fetch the most recent earnings transcript. Tries multiple sources."""
    symbol = ticker.upper()

    # Try direct scraping first (fast, no API cost)
    result = _scrape_motley_fool(symbol)
    if result:
        return result

    # Fallback: Claude web search (slower but handles edge cases)
    result = _fetch_via_claude(symbol)
    if result:
        return result

    print(f"  No transcript found for {symbol} via any method")
    return None


def _scrape_motley_fool(symbol: str) -> dict | None:
    """Scrape the latest earnings transcript from Motley Fool."""
    try:
        # Step 1: Try the Motley Fool earnings transcript listing page
        list_url = f"https://www.fool.com/earnings-call-transcripts/"
        resp = requests.get(list_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Search for a link matching this ticker
        symbol_lower = symbol.lower()
        transcript_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            link_text = a.get_text(strip=True).lower()
            # Match by ticker in URL slug or link text
            if "transcript" in href and (
                f"-{symbol_lower}-" in href
                or f"-{symbol_lower}/" in href
                or f"({symbol_lower})" in link_text
                or f" {symbol_lower} " in f" {link_text} "
            ):
                transcript_url = href
                break

        if not transcript_url:
            return None

        # Make URL absolute
        if transcript_url.startswith("/"):
            transcript_url = f"https://www.fool.com{transcript_url}"

        # Step 2: Fetch the transcript page
        resp2 = requests.get(transcript_url, headers=HEADERS, timeout=15)
        if resp2.status_code != 200:
            return None

        soup2 = BeautifulSoup(resp2.text, "html.parser")

        # Extract title for quarter/date info
        title = ""
        h1 = soup2.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        # Extract transcript body
        text = _extract_article_text(soup2)
        if not text or len(text) < 200:
            return None

        # Parse quarter and date from title
        quarter, date = _parse_quarter_from_title(title)

        # Truncate to keep within token limits
        if len(text) > 12000:
            text = text[:12000] + "\n\n[... transcript truncated for analysis ...]"

        return {
            "title": title or f"{symbol} Earnings Call Transcript",
            "quarter": quarter,
            "date": date,
            "company": _extract_company_from_title(title, symbol),
            "text": text,
        }
    except Exception as e:
        print(f"  Motley Fool scrape failed for {symbol}: {e}")
        return None


def _extract_article_text(soup: BeautifulSoup) -> str:
    """Extract the main article text from a Motley Fool page."""
    # Try known content selectors
    for selector in [
        "div.tailwind-article-body",
        "div.article-body",
        '[data-id="article-body"]',
        "div.content-body",
        "article",
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return text

    # Fallback: collect all substantial paragraphs
    paragraphs = []
    for p in soup.find_all("p"):
        t = p.get_text(strip=True)
        if len(t) > 40:
            paragraphs.append(t)
    return "\n\n".join(paragraphs)


def _parse_quarter_from_title(title: str) -> tuple[str | None, str | None]:
    """Extract quarter and date from a transcript title."""
    quarter = None
    date = None

    # Match patterns like "Q4 2025", "Q1 2026"
    q_match = re.search(r"(Q[1-4]\s*\d{4})", title, re.IGNORECASE)
    if q_match:
        quarter = q_match.group(1).upper()

    # Match patterns like "FY2025", "FY 2025"
    if not quarter:
        fy_match = re.search(r"(FY\s*\d{4})", title, re.IGNORECASE)
        if fy_match:
            quarter = fy_match.group(1).upper()

    return quarter, date


def _extract_company_from_title(title: str, symbol: str) -> str:
    """Extract company name from transcript title."""
    # Typical format: "Company Name (TICK) Q4 2025 Earnings Call Transcript"
    match = re.match(r"(.+?)\s*\(", title)
    if match:
        return match.group(1).strip()
    return symbol


def _fetch_via_claude(symbol: str) -> dict | None:
    """Fallback: use Claude with web search to find and summarize earnings."""
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=[{
                "role": "user",
                "content": (
                    f"I need information about {symbol}'s most recent quarterly earnings call. "
                    f"Please search for '{symbol} earnings call transcript' and "
                    f"'{symbol} quarterly earnings results'.\n\n"
                    "After finding the information, respond with:\n"
                    "Line 1: QUARTER: [e.g. Q4 2025]\n"
                    "Line 2: COMPANY: [full company name]\n\n"
                    "Then write a detailed summary of the earnings call covering:\n"
                    "- Revenue, EPS, and key financial metrics reported\n"
                    "- Management's guidance and strategic commentary\n"
                    "- Key risks and growth opportunities discussed\n"
                    "- Analyst questions and management responses\n"
                    "- Overall management tone\n\n"
                    "This is a very important analysis. Please be thorough."
                ),
            }],
        )

        # Collect all text blocks
        parts = []
        for block in response.content:
            if block.type == "text" and block.text.strip():
                parts.append(block.text.strip())
        text = "\n\n".join(parts)

        if not text or len(text) < 50:
            return None

        # Parse metadata
        quarter = None
        company = symbol
        q_match = re.search(r"QUARTER:\s*(.+)", text, re.IGNORECASE)
        if q_match:
            quarter = q_match.group(1).strip().strip("*").strip()
        c_match = re.search(r"COMPANY:\s*(.+)", text, re.IGNORECASE)
        if c_match:
            company = c_match.group(1).strip().strip("*").strip()

        # Also try to find quarter in the text itself if not in header
        if not quarter:
            q_match2 = re.search(r"(Q[1-4]\s*\d{4})", text)
            if q_match2:
                quarter = q_match2.group(1).upper()

        # Clean metadata lines from summary
        summary = re.sub(
            r"^(QUARTER:|COMPANY:|DATE:).*$", "", text, flags=re.MULTILINE
        ).strip()

        if len(summary) < 50:
            summary = text

        return {
            "title": f"{company} ({symbol}) Earnings Call Summary",
            "quarter": quarter,
            "date": None,
            "company": company,
            "text": summary,
        }
    except Exception as e:
        print(f"  Claude transcript fallback failed for {symbol}: {e}")
        return None
