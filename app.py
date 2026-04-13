"""TickerLens — AI-powered equity analysis platform built with Streamlit."""

import streamlit as st
from modules_py.fetch_metrics import fetch_metrics
from modules_py.fetch_transcript import fetch_transcript
from modules_py.analyze_transcript import analyze_transcript
from modules_py.scoring import score_valuation, score_profitability, score_risk_momentum, compute_overall
from modules_py.industry_map import resolve_industry, get_sector_medians, get_industry_name

# ── Page config ──
st.set_page_config(page_title="TickerLens", page_icon="🔍", layout="centered")

# ── Custom CSS for dark finance theme ──
st.markdown("""
<style>
    .stApp { background-color: #0f1117; }

    .title-text {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #58a6ff, #3fb950);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle-text {
        text-align: center;
        color: #8b949e;
        font-size: 1.05rem;
        margin-top: 0;
    }

    .signal-badge {
        display: inline-block;
        padding: 0.35rem 1.2rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.1rem;
        text-transform: uppercase;
    }
    .signal-green  { background: rgba(35,54,34,0.6); color: #3fb950; border: 1px solid #3fb950; }
    .signal-yellow { background: rgba(61,46,0,0.3);  color: #d29922; border: 1px solid #d29922; }
    .signal-red    { background: rgba(54,34,34,0.3);  color: #f85149; border: 1px solid #f85149; }

    .pillar-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.2rem;
        height: 100%;
    }
    .pillar-title {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
    }
    .pillar-score {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .pillar-reasoning {
        font-size: 0.82rem;
        color: #8b949e;
        line-height: 1.45;
        margin-top: 0.5rem;
    }

    .score-bar {
        height: 6px;
        border-radius: 3px;
        background: #21262d;
        margin: 0.4rem 0 0.6rem;
        overflow: hidden;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 3px;
    }

    .overall-box {
        text-align: center;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #30363d;
        background: #161b22;
        margin-bottom: 1.5rem;
    }

    .metric-row {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 0.6rem;
        color: #8b949e;
        font-size: 0.9rem;
    }

    footer { text-align: center; color: #484f58; font-size: 0.8rem; padding: 2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown('<p class="title-text">TickerLens</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Instant, AI-powered equity analysis</p>', unsafe_allow_html=True)

# ── Ticker input ──
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ticker_input = st.text_input(
        "Enter a stock ticker",
        placeholder="e.g. AAPL, NVDA, TSLA",
        max_chars=5,
        label_visibility="collapsed",
    ).upper().strip()
    analyze_clicked = st.button("Analyze", use_container_width=True, type="primary")


def signal_color(signal):
    return {"Green": "#3fb950", "Yellow": "#d29922", "Red": "#f85149"}.get(signal, "#8b949e")


def signal_class(signal):
    return f"signal-{signal.lower()}"


def render_pillar(pillar):
    color = signal_color(pillar["signal"])
    width = pillar["score"] * 10
    st.markdown(f"""
    <div class="pillar-card">
        <div class="pillar-title">{pillar["name"]}</div>
        <div class="pillar-score" style="color:{color}">{pillar["score"]}/10</div>
        <div class="score-bar">
            <div class="score-bar-fill" style="width:{width}%; background:{color}"></div>
        </div>
        <span class="signal-badge {signal_class(pillar["signal"])}" style="font-size:0.75rem">{pillar["signal"]}</span>
        <div class="pillar-reasoning">{pillar["reasoning"]}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Analysis pipeline ──
if analyze_clicked and ticker_input:
    with st.spinner("Analyzing... this may take 15–30 seconds."):
        try:
            # 1. Fetch live metrics via yfinance
            metrics = fetch_metrics(ticker_input)

            # 2. Resolve FF48 industry
            ff48 = resolve_industry(metrics.get("industry"))
            medians = get_sector_medians(ff48)
            industry_name = get_industry_name(ff48)

            fallback_medians = medians or {
                "pe_inc": 20, "bm": 0.4, "evm": 12,
                "grossMargin": 0.3, "netMargin": 0.08, "quickRatio": 1.2,
            }

            # 3. Score quantitative pillars
            valuation = score_valuation(metrics, fallback_medians)
            profitability = score_profitability(metrics, fallback_medians)
            risk_momentum = score_risk_momentum(metrics, fallback_medians)

            # 4. Fetch transcript + sentiment (Claude AI)
            transcript = fetch_transcript(ticker_input)
            sentiment = analyze_transcript(ticker_input, transcript["text"] if transcript else None)

            # Add transcript quarter/date to the sentiment reasoning
            if transcript and transcript.get("quarter"):
                quarter_label = transcript["quarter"]
                if transcript.get("date"):
                    quarter_label += f" ({transcript['date']})"
                sentiment["reasoning"] = f"[{quarter_label}] {sentiment['reasoning']}"

            # 5. Compute overall
            pillars = [valuation, profitability, risk_momentum, sentiment]
            overall = compute_overall(pillars)

            # ── Render results ──
            sector_label = industry_name or metrics.get("industry") or "broad market"
            price_str = f"${metrics['currentPrice']:,.2f}" if metrics.get("currentPrice") else "N/A"
            mcap = metrics.get("marketCap")
            if mcap:
                if mcap >= 1e12:
                    mcap_str = f"${mcap/1e12:.2f}T"
                elif mcap >= 1e9:
                    mcap_str = f"${mcap/1e9:.1f}B"
                else:
                    mcap_str = f"${mcap/1e6:.0f}M"
            else:
                mcap_str = "N/A"

            st.markdown(f"""
            <div class="overall-box">
                <h2 style="margin:0 0 0.3rem; color:#e1e4e8">{metrics["name"]} ({ticker_input})</h2>
                <div class="metric-row">
                    <span>Price: {price_str}</span>
                    <span>Market Cap: {mcap_str}</span>
                    <span>Sector: {sector_label}</span>
                </div>
                <div style="margin-top:1rem">
                    <span class="signal-badge {signal_class(overall["signal"])}" style="font-size:1.2rem">
                        {overall["signal"]} — {overall["score"]}/10
                    </span>
                </div>
                <p style="margin-top:0.8rem; color:#8b949e; font-size:0.9rem">
                    {" | ".join(f'{p["name"]}: {p["signal"]} ({p["score"]}/10)' for p in pillars)}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Pillar cards in a 2x2 grid
            col_a, col_b = st.columns(2)
            with col_a:
                render_pillar(pillars[0])
            with col_b:
                render_pillar(pillars[1])

            col_c, col_d = st.columns(2)
            with col_c:
                render_pillar(pillars[2])
            with col_d:
                render_pillar(pillars[3])

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Analysis failed: {e}")

# ── Footer ──
st.markdown('<footer>TickerLens — Built for FIN 372, UT Austin</footer>', unsafe_allow_html=True)
