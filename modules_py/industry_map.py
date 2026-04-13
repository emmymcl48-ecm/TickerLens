"""Map stock industries to Fama-French 48 sectors and retrieve sector medians."""

import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sectorData.json")
with open(_DATA_PATH, "r") as f:
    _SECTOR_DATA = json.load(f)


YAHOO_TO_FF48 = {
    # Technology
    "consumer electronics": "CHIPS",
    "semiconductors": "CHIPS",
    "semiconductor equipment": "CHIPS",
    "software - infrastructure": "BUSSV",
    "software - application": "BUSSV",
    "information technology services": "BUSSV",
    "internet content & information": "BUSSV",
    "internet retail": "RTAIL",
    "electronic components": "CHIPS",
    "scientific & technical instruments": "CHIPS",
    "computer hardware": "COMPS",
    "communication equipment": "TELCM",
    # Healthcare
    "drug manufacturers - general": "DRUGS",
    "drug manufacturers - specialty & generic": "DRUGS",
    "biotechnology": "DRUGS",
    "medical devices": "MEDEQ",
    "health information services": "HLTH",
    "healthcare plans": "HLTH",
    "medical care facilities": "HLTH",
    "diagnostics & research": "MEDEQ",
    # Finance
    "banks - diversified": "BANKS",
    "banks - regional": "BANKS",
    "credit services": "FIN",
    "insurance - diversified": "INSUR",
    "insurance - life": "INSUR",
    "insurance - property & casualty": "INSUR",
    "capital markets": "FIN",
    "financial data & stock exchanges": "FIN",
    "asset management": "FIN",
    "real estate services": "RLEST",
    "reit - specialty": "RLEST",
    "reit - residential": "RLEST",
    "reit - industrial": "RLEST",
    "reit - retail": "RLEST",
    "reit - diversified": "RLEST",
    "reit - office": "RLEST",
    "reit - healthcare facilities": "RLEST",
    # Consumer
    "auto manufacturers": "AUTOS",
    "auto parts": "AUTOS",
    "restaurants": "MEALS",
    "packaged foods": "FOOD",
    "beverages - non-alcoholic": "SODA",
    "beverages - brewers": "BEER",
    "household & personal products": "HSHLD",
    "discount stores": "RTAIL",
    "specialty retail": "RTAIL",
    "home improvement retail": "RTAIL",
    "apparel retail": "RTAIL",
    "grocery stores": "RTAIL",
    "department stores": "RTAIL",
    "apparel manufacturing": "CLTHS",
    # Industrial
    "aerospace & defense": "AERO",
    "industrial distribution": "WHLSL",
    "conglomerates": "OTHER",
    "farm & heavy construction machinery": "MACH",
    "specialty industrial machinery": "MACH",
    "electrical equipment & parts": "ELCEQ",
    "building products & equipment": "BLDMT",
    # Energy
    "oil & gas integrated": "OIL",
    "oil & gas e&p": "OIL",
    "oil & gas midstream": "OIL",
    "oil & gas equipment & services": "OIL",
    "oil & gas refining & marketing": "OIL",
    # Utilities
    "utilities - regulated electric": "UTIL",
    "utilities - diversified": "UTIL",
    "utilities - renewable": "UTIL",
    # Telecom
    "telecom services": "TELCM",
    # Entertainment / Media
    "entertainment": "FUN",
    "electronic gaming & multimedia": "FUN",
    "advertising agencies": "BUSSV",
    "broadcasting": "BOOKS",
    "publishing": "BOOKS",
}


def resolve_industry(yahoo_industry: str | None) -> str | None:
    """Map a Yahoo Finance industry string to an FF48 abbreviation."""
    if not yahoo_industry:
        return None
    return YAHOO_TO_FF48.get(yahoo_industry.lower())


def get_sector_medians(ff48_abbr: str | None) -> dict | None:
    """Get median financial metrics for a given FF48 industry."""
    if not ff48_abbr:
        return None
    return _SECTOR_DATA["industryMedians"].get(ff48_abbr.upper())


def get_industry_name(ff48_abbr: str | None) -> str | None:
    """Get the full industry name from FF48 abbreviation."""
    if not ff48_abbr:
        return None
    return _SECTOR_DATA["ff48Names"].get(ff48_abbr.upper(), ff48_abbr)
