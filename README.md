# Nifty 250 Swing + Intraday Scanner

Streamlit-based scanner using Angel One SmartAPI.

## Features
- Swing scanning (EMA, RSI, MACD, Breakout, Volume)
- Intraday scanning (VWAP, ORB, EMA)
- Nifty regime + ADX filter (toggle)
- Sector strength/weakness (toggle)
- Backtesting engine
- Mobile-first UI

## Setup
1. `pip install -r requirements.txt`
2. Add Angel One credentials in `.streamlit/secrets.toml`
3. `streamlit run app.py`
