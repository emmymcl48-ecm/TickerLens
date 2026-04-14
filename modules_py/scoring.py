"""Scoring engine: compare stock metrics against sector medians to produce pillar scores."""


def score_vs_median(value, median, direction="lower"):
    """Score a metric relative to its sector median (1-10 scale).

    Uses a gentler slope (4) centered at 5 so that moderate deviations
    from the median don't immediately slam to 1 or 10.
    """
    if value is None or median is None or median == 0:
        return None
    ratio = value / median
    if direction == "lower":
        raw = 5 + (1 - ratio) * 4
    else:
        raw = 5 + (ratio - 1) * 4
    return max(1, min(10, round(raw)))


def avg_score(scores):
    """Average a list of scores, ignoring Nones."""
    valid = [s for s in scores if s is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def score_to_signal(score):
    if score is None:
        return "Yellow"
    if score >= 6.5:
        return "Green"
    if score >= 4.0:
        return "Yellow"
    return "Red"


def score_valuation(metrics, medians):
    scores, reasons = [], []

    pe = score_vs_median(metrics.get("trailingPE"), medians.get("pe_inc"), "lower")
    if pe is not None:
        scores.append(pe)
        m_pe, s_pe = metrics["trailingPE"], medians["pe_inc"]
        reasons.append(f"P/E {m_pe:.1f} vs sector median {s_pe:.1f} ({'below' if m_pe < s_pe else 'above'})")

    pb = metrics.get("priceToBook")
    bm_med = medians.get("bm")
    if pb and bm_med and bm_med > 0 and pb > 0:
        stock_bm = 1 / pb
        bm_score = score_vs_median(stock_bm, bm_med, "higher")
        scores.append(bm_score)
        reasons.append(f"B/M {stock_bm:.3f} vs sector {bm_med:.3f}")

    ev = score_vs_median(metrics.get("enterpriseToEbitda"), medians.get("evm"), "lower")
    if ev is not None:
        scores.append(ev)
        reasons.append(f"EV/EBITDA {metrics['enterpriseToEbitda']:.1f} vs sector {medians['evm']:.1f}")

    avg = avg_score(scores)
    return {
        "name": "Valuation",
        "score": round(avg, 1) if avg else 5.0,
        "signal": score_to_signal(avg),
        "reasoning": ". ".join(reasons) + "." if reasons else "Insufficient valuation data.",
    }


def score_profitability(metrics, medians):
    scores, reasons = [], []

    gm = metrics.get("grossMargin")
    gm_med = medians.get("grossMargin")
    if gm is not None and gm_med is not None:
        scores.append(score_vs_median(gm, gm_med, "higher"))
        reasons.append(f"Gross margin {gm*100:.1f}% vs sector {gm_med*100:.1f}%")

    nm = metrics.get("netMargin")
    nm_med = medians.get("netMargin")
    if nm is not None and nm_med is not None:
        scores.append(score_vs_median(nm, nm_med, "higher"))
        reasons.append(f"Net margin {nm*100:.1f}% vs sector {nm_med*100:.1f}%")

    roe = metrics.get("returnOnEquity")
    roic_med = medians.get("returnOnInvestedCapital")
    if roe is not None and roic_med is not None and roic_med != 0:
        scores.append(score_vs_median(roe, roic_med, "higher"))
        reasons.append(f"ROE {roe*100:.1f}% vs sector ROIC {roic_med*100:.1f}%")
    elif roe is not None:
        s = max(1, min(10, round(5 + roe * 15)))
        scores.append(s)
        reasons.append(f"ROE {roe*100:.1f}%")

    rg = metrics.get("revenueGrowth")
    if rg is not None:
        s = max(1, min(10, round(5 + rg * 8)))
        scores.append(s)
        reasons.append(f"Revenue growth {rg*100:.1f}%")

    avg = avg_score(scores)
    return {
        "name": "Profitability",
        "score": round(avg, 1) if avg else 5.0,
        "signal": score_to_signal(avg),
        "reasoning": ". ".join(reasons) + "." if reasons else "Insufficient profitability data.",
    }


def score_risk_momentum(metrics, medians):
    scores, reasons = [], []

    qr = metrics.get("quickRatio")
    qr_med = medians.get("quickRatio")
    if qr is not None and qr_med is not None:
        scores.append(score_vs_median(qr, qr_med, "higher"))
        reasons.append(f"Quick ratio {qr:.2f} vs sector {qr_med:.2f}")

    de = metrics.get("debtToEquity")
    if de is not None:
        s = max(1, min(10, round(8 - de / 40)))
        scores.append(s)
        reasons.append(f"Debt/Equity {de:.0f}%")

    beta = metrics.get("beta")
    if beta is not None:
        s = max(1, min(10, round(8 - (beta - 0.5) * 3)))
        scores.append(s)
        reasons.append(f"Beta {beta:.2f}")

    price = metrics.get("currentPrice")
    avg200 = metrics.get("twoHundredDayAvg")
    if price and avg200 and avg200 > 0:
        momentum = (price - avg200) / avg200
        s = max(1, min(10, round(5 + momentum * 15)))
        scores.append(s)
        reasons.append(f"Price {'+' if momentum >= 0 else ''}{momentum*100:.1f}% vs 200-day avg")

    avg = avg_score(scores)
    return {
        "name": "Risk & Momentum",
        "score": round(avg, 1) if avg else 5.0,
        "signal": score_to_signal(avg),
        "reasoning": ". ".join(reasons) + "." if reasons else "Insufficient risk data.",
    }


def compute_overall(pillars):
    weights = {
        "Valuation": 0.30,
        "Profitability": 0.30,
        "Risk & Momentum": 0.20,
        "Earnings Sentiment": 0.20,
    }
    total_weight = 0
    weighted_sum = 0
    for p in pillars:
        w = weights.get(p["name"], 0.25)
        weighted_sum += p["score"] * w
        total_weight += w
    overall = weighted_sum / total_weight if total_weight > 0 else 5.0
    return {
        "score": round(overall, 1),
        "signal": score_to_signal(overall),
    }
