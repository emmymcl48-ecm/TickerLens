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
    "semiconductor equipment & materials": "CHIPS",
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
    "data storage": "COMPS",
    "electronics & computer distribution": "WHLSL",
    "solar": "ELCEQ",
    # Healthcare
    "drug manufacturers - general": "DRUGS",
    "drug manufacturers - specialty & generic": "DRUGS",
    "biotechnology": "DRUGS",
    "medical devices": "MEDEQ",
    "medical instruments & supplies": "MEDEQ",
    "health information services": "HLTH",
    "healthcare plans": "HLTH",
    "medical care facilities": "HLTH",
    "medical distribution": "HLTH",
    "diagnostics & research": "MEDEQ",
    "pharmaceutical retailers": "RTAIL",
    # Finance
    "banks - diversified": "BANKS",
    "banks - regional": "BANKS",
    "mortgage finance": "BANKS",
    "credit services": "FIN",
    "insurance - diversified": "INSUR",
    "insurance - life": "INSUR",
    "insurance - property & casualty": "INSUR",
    "insurance - reinsurance": "INSUR",
    "insurance - specialty": "INSUR",
    "insurance brokers": "INSUR",
    "capital markets": "FIN",
    "financial data & stock exchanges": "FIN",
    "financial conglomerates": "FIN",
    "asset management": "FIN",
    "shell companies": "FIN",
    "real estate services": "RLEST",
    "real estate - development": "RLEST",
    "real estate - diversified": "RLEST",
    "reit - specialty": "RLEST",
    "reit - residential": "RLEST",
    "reit - industrial": "RLEST",
    "reit - retail": "RLEST",
    "reit - diversified": "RLEST",
    "reit - office": "RLEST",
    "reit - healthcare facilities": "RLEST",
    "reit - hotel & motel": "RLEST",
    "reit - mortgage": "RLEST",
    # Consumer Cyclical
    "auto manufacturers": "AUTOS",
    "auto parts": "AUTOS",
    "auto & truck dealerships": "AUTOS",
    "recreational vehicles": "AUTOS",
    "restaurants": "MEALS",
    "packaged foods": "FOOD",
    "confectioners": "FOOD",
    "farm products": "AGRIC",
    "beverages - non-alcoholic": "SODA",
    "beverages - brewers": "BEER",
    "beverages - wineries & distilleries": "BEER",
    "household & personal products": "HSHLD",
    "tobacco": "SMOKE",
    "discount stores": "RTAIL",
    "specialty retail": "RTAIL",
    "home improvement retail": "RTAIL",
    "apparel retail": "RTAIL",
    "grocery stores": "RTAIL",
    "department stores": "RTAIL",
    "luxury goods": "RTAIL",
    "apparel manufacturing": "CLTHS",
    "footwear & accessories": "CLTHS",
    "textile manufacturing": "CLTHS",
    "furnishings, fixtures & appliances": "HSHLD",
    "packaging & containers": "BOXES",
    "personal services": "PERSV",
    "education & training services": "PERSV",
    "staffing & employment services": "BUSSV",
    "consulting services": "BUSSV",
    "rental & leasing services": "BUSSV",
    "gambling": "FUN",
    "resorts & casinos": "FUN",
    "leisure": "FUN",
    "lodging": "MEALS",
    "travel services": "FUN",
    # Industrial
    "aerospace & defense": "AERO",
    "airlines": "TRANS",
    "railroads": "TRANS",
    "trucking": "TRANS",
    "marine shipping": "SHIPS",
    "integrated freight & logistics": "TRANS",
    "industrial distribution": "WHLSL",
    "conglomerates": "OTHER",
    "farm & heavy construction machinery": "MACH",
    "specialty industrial machinery": "MACH",
    "tools & accessories": "MACH",
    "electrical equipment & parts": "ELCEQ",
    "building products & equipment": "BLDMT",
    "engineering & construction": "CNSTR",
    "waste management": "BUSSV",
    "security & protection services": "BUSSV",
    "metal fabrication": "STEEL",
    "steel": "STEEL",
    "aluminum": "STEEL",
    "copper": "STEEL",
    "other industrial metals & mining": "MINES",
    "gold": "GOLD",
    "silver": "GOLD",
    "specialty chemicals": "CHEMS",
    "agricultural inputs": "CHEMS",
    "chemicals": "CHEMS",
    "paper & paper products": "PAPER",
    "lumber & wood production": "PAPER",
    # Energy
    "oil & gas integrated": "OIL",
    "oil & gas e&p": "OIL",
    "oil & gas midstream": "OIL",
    "oil & gas equipment & services": "OIL",
    "oil & gas refining & marketing": "OIL",
    "oil & gas drilling": "OIL",
    "thermal coal": "COAL",
    "uranium": "MINES",
    # Utilities
    "utilities - regulated electric": "UTIL",
    "utilities - regulated gas": "UTIL",
    "utilities - regulated water": "UTIL",
    "utilities - diversified": "UTIL",
    "utilities - renewable": "UTIL",
    "utilities - independent power producers": "UTIL",
    # Telecom
    "telecom services": "TELCM",
    "pay tv": "TELCM",
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
