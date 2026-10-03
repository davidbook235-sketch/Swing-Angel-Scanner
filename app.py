import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data_layer.angel_client import AngelDataClient
from data_layer.universe import load_nifty250, get_token
from analysis.swing_scanner import scan_universe, compute_swing_signals
from analysis.intraday_scanner import compute_intraday_signals
from analysis.regime import get_nifty_regime, apply_regime_filter
from analysis.sector_strength import compute_sector_strength, get_stock_sector_boost
from backtest.engine import generate_backtest_signals, run_backtest


st.set_page_config(
    page_title="Nifty 250 Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Mobile-First CSS ───
st.markdown("""
<style>
    @media (max-width: 600px) {
        .stButton > button { min-height: 48px; font-size: 1rem; }
        .stMetric { font-size: 0.85rem !important; }
        .stDataFrame { font-size: 0.75rem; }
    }
    .stButton > button { border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { padding: 12px 16px; }
</style>
""", unsafe_allow_html=True)


# ─── Cached Client ───
@st.cache_resource
def get_client():
    return AngelDataClient()


@st.cache_data(ttl=300)
def cached_scan(interval, days, mode):
    client = get_client()
    universe = load_nifty250()
    if universe.empty:
        return pd.DataFrame()
    return scan_universe(client, universe, interval=interval, days=days)


# ─── Session State ───
if "client_ready" not in st.session_state:
    st.session_state.client_ready = True


# ─── Sidebar ───
with st.sidebar:
    st.title("⚙️ Settings")
    scan_mode = st.radio("Scan Mode", ["Swing", "Intraday"], horizontal=True)

    st.divider()
    st.subheader("Filters")
    regime_on = st.toggle("Nifty Regime & ADX Filter", value=True)
    sector_on = st.toggle("Sector Strength Filter", value=True)
    backtest_on = st.toggle("Backtest Mode", value=False)

    st.divider()
    min_score = st.slider("Minimum Score", 1, 5, 3)
    adx_threshold = st.slider("ADX Threshold", 15, 40, 25)

    st.divider()
    if st.button("🔄 Refresh Scan", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─── Main ───
st.title("📈 Nifty 250 Swing + Intraday Scanner")

try:
    client = get_client()
except Exception as e:
    st.error(f"Angel One login failed: {e}")
    st.stop()


# Nifty Regime
regime = {"regime": "UNKNOWN", "adx": 0, "advice": "", "is_trending": False}
nifty_df = pd.DataFrame()
if regime_on:
    nifty_df = client.get_historical("99926000", "ONE_DAY", 100)
    if not nifty_df.empty:
        regime = get_nifty_regime(nifty_df, adx_threshold)
        color = "🟢" if regime["regime"] == "TRENDING_UP" else (
            "🔴" if regime["regime"] == "TRENDING_DOWN" else "🟡")
        st.info(f"{color} **Regime**: {regime['regime']} | ADX: {regime['adx']} | {regime['advice']}")


# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Scanner", "🔥 Sectors", "📉 Backtest", "📈 Charts"])


with tab1:
    interval = "ONE_DAY" if scan_mode == "Swing" else "FIVE_MINUTE"
    days = 200 if scan_mode == "Swing" else 5

    with st.spinner(f"Scanning Nifty 250 ({scan_mode})..."):
        results = cached_scan(interval, days, scan_mode)

    if results.empty:
        st.warning("No signals found or data fetch failed.")
    else:
        # Regime filter
        if regime_on and scan_mode == "Swing":
            results = apply_regime_filter(results, regime, True)

        # Sector boost
        if sector_on and scan_mode == "Swing" and not nifty_df.empty:
            sector_df = compute_sector_strength(client, nifty_df)
            results["Sector_Boost"] = results.apply(
                lambda r: get_stock_sector_boost(r.get("Sector", ""), sector_df), axis=1
            )
            results["Final_Score"] = results["Score"] + results["Sector_Boost"]
            results = results.sort_values("Final_Score", ascending=False)

        results = results[results["Score"] >= min_score]
        st.success(f"Found {len(results)} signals")
        st.dataframe(results, use_container_width=True, hide_index=True)


with tab2:
    st.subheader("Sector Strength Heatmap")
    if nifty_df.empty:
        nifty_df = client.get_historical("99926000", "ONE_DAY", 100)

    sector_df = compute_sector_strength(client, nifty_df)

    if not sector_df.empty:
        fig = go.Figure(data=go.Heatmap(
            z=sector_df[["1M_Return_%", "3M_Return_%"]].values,
            x=["1M Return", "3M Return"],
            y=sector_df["Sector"].tolist(),
            colorscale="RdYlGn",
            text=sector_df[["1M_Return_%", "3M_Return_%"]].values,
            texttemplate="%{text:.1f}%",
        ))
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(sector_df, use_container_width=True, hide_index=True)


with tab3:
    if not backtest_on:
        st.info("Enable **Backtest Mode** from sidebar.")
    else:
        st.subheader("Strategy Backtest")
        universe = load_nifty250()
        symbol = st.selectbox("Select Stock", universe["Symbol"].tolist()[:50])
        token = get_token(symbol)

        if token:
            bt_df = client.get_historical(token, "ONE_DAY", 365)
            if not bt_df.empty:
                signals = generate_backtest_signals(bt_df, "swing")
                metrics = run_backtest(bt_df, signals)

                c1, c2, c3 = st.columns(3)
                c1.metric("Return", f"{metrics['Total_Return_%']}%")
                c2.metric("Sharpe", metrics["Sharpe_Ratio"])
                c3.metric("Win Rate", f"{metrics['Win_Rate_%']}%")

                c4, c5, c6 = st.columns(3)
                c4.metric("Max DD", f"{metrics['Max_Drawdown_%']}%")
                c5.metric("Trades", metrics["Total_Trades"])
                c6.metric("Profit Factor", metrics["Profit_Factor"])


with tab4:
    st.subheader("Candlestick Chart")
    universe = load_nifty250()
    symbol = st.selectbox("Stock", universe["Symbol"].tolist()[:50], key="chart_sym")
    token = get_token(symbol)

    if token:
        chart_df = client.get_historical(token, "ONE_DAY", 100)
        if not chart_df.empty:
            fig = go.Figure(data=[
                go.Candlestick(
                    x=chart_df["timestamp"],
                    open=chart_df["open"], high=chart_df["high"],
                    low=chart_df["low"], close=chart_df["close"],
                    name="OHLC"
                )
            ])
            fig.update_layout(
                height=400,
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
