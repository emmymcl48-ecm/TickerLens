"""TickerLens — AI-powered equity analysis platform built with Streamlit."""

import re
from datetime import datetime
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from modules_py.fetch_metrics import fetch_metrics
from modules_py.earnings_sentiment import get_earnings_sentiment
from modules_py.claude_combined import fetch_metrics_and_sentiment
from modules_py.scoring import score_valuation, score_profitability, score_risk_momentum, compute_overall
from modules_py.industry_map import resolve_industry, get_sector_medians, get_industry_name


# ── Cached wrappers (avoid redundant API calls on reruns) ──
@st.cache_data(ttl=300, show_spinner=False)
def cached_fetch_metrics(ticker):
    return fetch_metrics(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def cached_earnings_sentiment(ticker):
    return get_earnings_sentiment(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def cached_metrics_and_sentiment(ticker):
    return fetch_metrics_and_sentiment(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def cached_price_history(ticker, period="1y"):
    """Fetch daily price history from yfinance."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return None
        return hist
    except Exception:
        return None


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
        max_chars=6,
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
    # Validate ticker format before hitting any APIs
    if not re.match(r'^[A-Z]{1,5}(\.[A-Z])?$', ticker_input):
        st.error("Invalid ticker format. Use 1-5 letters (e.g. AAPL, NVDA, BRK.B).")
        st.stop()

    with st.spinner("Analyzing... this may take 15-30 seconds."):
        try:
            # 1. Try yfinance for current metrics (fast, free)
            metrics = cached_fetch_metrics(ticker_input)

            if metrics:
                sentiment = cached_earnings_sentiment(ticker_input)
            else:
                metrics, sentiment = cached_metrics_and_sentiment(ticker_input)

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

            # 4. Compute overall
            pillars = [valuation, profitability, risk_momentum, sentiment]
            overall = compute_overall(pillars)

            # 5. Format display values
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

            # Store in session state so results persist across reruns
            st.session_state["analysis"] = {
                "ticker": ticker_input,
                "metrics": metrics,
                "pillars": pillars,
                "overall": overall,
                "sector_label": sector_label,
                "price_str": price_str,
                "mcap_str": mcap_str,
            }
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Analysis failed: {e}")


# ── Render results (persists across reruns for interactive elements) ──
if "analysis" in st.session_state:
    a = st.session_state["analysis"]
    ticker = a["ticker"]
    metrics = a["metrics"]
    pillars = a["pillars"]
    overall = a["overall"]

    st.markdown(f"""
    <div class="overall-box">
        <h2 style="margin:0 0 0.3rem; color:#e1e4e8">{metrics["name"]} ({ticker})</h2>
        <div class="metric-row">
            <span>Price: {a["price_str"]}</span>
            <span>Market Cap: {a["mcap_str"]}</span>
            <span>Sector: {a["sector_label"]}</span>
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

    # ── Price chart ──
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    period_labels = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"}
    chart_cols = st.columns(len(period_labels))
    selected_period = st.session_state.get("chart_period", "1Y")
    for i, label in enumerate(period_labels):
        if chart_cols[i].button(label, use_container_width=True,
                                type="primary" if label == selected_period else "secondary",
                                key=f"period_{label}"):
            st.session_state["chart_period"] = label
            st.rerun()

    hist = cached_price_history(ticker, period_labels[selected_period])
    if hist is not None and not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist["Close"],
            mode="lines",
            line=dict(color="#3fb950", width=2),
            fill="tozeroy",
            fillcolor="rgba(63,185,80,0.08)",
            hovertemplate="%{x|%b %d, %Y}<br>$%{y:,.2f}<extra></extra>",
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0f1117",
            plot_bgcolor="#0f1117",
            margin=dict(l=0, r=0, t=10, b=0),
            height=300,
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False,
                       tickprefix="$"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Price history unavailable for this ticker.")

    # ── Peer comparison ──
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    with st.expander("Compare with peers"):
        peer_input = st.text_input(
            "Enter peer tickers (comma-separated)",
            placeholder="e.g. MSFT, GOOG, META",
            key="peer_input",
            label_visibility="collapsed",
        )
        if peer_input:
            peers = [t.strip().upper() for t in peer_input.split(",") if t.strip()]
            peers = [t for t in peers if re.match(r'^[A-Z]{1,5}(\.[A-Z])?$', t)]

            if peers:
                all_tickers = [ticker] + peers[:4]
                all_metrics = {ticker: metrics}
                for p in peers[:4]:
                    pm = cached_fetch_metrics(p)
                    if not pm:
                        # yfinance blocked — fall back to Claude
                        try:
                            pm, _ = cached_metrics_and_sentiment(p)
                        except Exception:
                            pm = None
                    if pm:
                        all_metrics[p] = pm

                rows = []
                display_fields = [
                    ("Price", "currentPrice", "${:,.2f}"),
                    ("P/E", "trailingPE", "{:.1f}"),
                    ("P/B", "priceToBook", "{:.2f}"),
                    ("EV/EBITDA", "enterpriseToEbitda", "{:.1f}"),
                    ("Gross Margin", "grossMargin", "{:.1%}"),
                    ("Net Margin", "netMargin", "{:.1%}"),
                    ("ROE", "returnOnEquity", "{:.1%}"),
                    ("D/E", "debtToEquity", "{:.0f}%"),
                    ("Beta", "beta", "{:.2f}"),
                    ("Rev Growth", "revenueGrowth", "{:.1%}"),
                ]
                for label, key, fmt in display_fields:
                    row = {"Metric": label}
                    for t in all_tickers:
                        m = all_metrics.get(t)
                        if m and m.get(key) is not None:
                            try:
                                if key == "debtToEquity":
                                    row[t] = f"{m[key]:.0f}%"
                                else:
                                    row[t] = fmt.format(m[key])
                            except (ValueError, TypeError):
                                row[t] = "N/A"
                        else:
                            row[t] = "N/A"
                    rows.append(row)

                st.table(rows)
                missing = [t for t in peers if t not in all_metrics]
                if missing:
                    st.caption(f"Could not fetch data for: {', '.join(missing)}")

    # ── Data sources ──
    data_source = metrics.get("dataSource", "Unknown")
    data_date = metrics.get("dataDate", "Unknown")
    sector_source = "WRDS / Compustat (Fama-French 48 Industry Medians)"

    st.markdown(f"""
    <div style="margin-top:1.5rem; padding:1rem; background:#161b22;
                border:1px solid #30363d; border-radius:10px;">
        <div style="font-size:0.8rem; color:#8b949e; text-transform:uppercase;
                    letter-spacing:0.05em; margin-bottom:0.5rem;">
            Data Sources
        </div>
        <div style="font-size:0.85rem; color:#c9d1d9; line-height:1.7;">
            <span style="color:#58a6ff;">Financial Metrics:</span> {data_source} — retrieved {data_date}<br>
            <span style="color:#58a6ff;">Sector Benchmarks:</span> {sector_source}<br>
            <span style="color:#58a6ff;">Earnings Sentiment:</span> Claude AI (Anthropic) with web search
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Downloadable report ──
    report_lines = [
        "TickerLens Analysis Report",
        "=" * 40,
        f"Company:    {metrics['name']} ({ticker})",
        f"Price:      {a['price_str']}",
        f"Market Cap: {a['mcap_str']}",
        f"Sector:     {a['sector_label']}",
        f"Date:       {data_date}",
        "",
        f"OVERALL SIGNAL: {overall['signal']} — {overall['score']}/10",
        "",
    ]
    for p in pillars:
        report_lines.append(f"--- {p['name']} ---")
        report_lines.append(f"  Score:  {p['score']}/10  ({p['signal']})")
        report_lines.append(f"  Detail: {p['reasoning']}")
        report_lines.append("")
    report_lines.append(f"Data Source: {data_source}")
    report_lines.append(f"Sector Benchmarks: {sector_source}")
    report_lines.append("Earnings Sentiment: Claude AI (Anthropic)")
    report_lines.append("\nGenerated by TickerLens — FIN 372, UT Austin")
    report_text = "\n".join(report_lines)

    st.download_button(
        label="Download Report",
        data=report_text,
        file_name=f"TickerLens_{ticker}_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True,
    )

# ── Footer ──
st.markdown('<footer>TickerLens — Built for FIN 372, UT Austin</footer>', unsafe_allow_html=True)
