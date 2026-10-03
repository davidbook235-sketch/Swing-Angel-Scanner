import time
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange


def compute_swing_signals(df):
    if len(df) < 50:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    ema20 = EMAIndicator(close, window=20).ema_indicator()
    ema50 = EMAIndicator(close, window=50).ema_indicator()
    rsi = RSIIndicator(close, window=14).rsi()
    macd_ind = MACD(close, window_slow=26, window_fast=12, window_sign=9)
    macd_line = macd_ind.macd()
    macd_signal = macd_ind.macd_signal()
    adx = ADXIndicator(high, low, close, window=14).adx()
    atr = AverageTrueRange(high, low, close, window=14).average_true_range()

    high_20 = high.rolling(20).max().shift(1)
    breakout = close > high_20

    vol_avg = volume.rolling(20).mean()
    vol_spike = volume > (vol_avg * 2)

    score = 0
    reasons = []

    if ema20.iloc[-1] > ema50.iloc[-1]:
        score += 1
        reasons.append("EMA20 > EMA50")
    if rsi.iloc[-1] > 55:
        score += 1
        reasons.append("RSI > 55")
    if macd_line.iloc[-1] > macd_signal.iloc[-1]:
        score += 1
        reasons.append("MACD bullish")
    if breakout.iloc[-1]:
        score += 1
        reasons.append("20-day breakout")
    if vol_spike.iloc[-1]:
        score += 1
        reasons.append("Volume spike")

    entry = close.iloc[-1]
    stop_loss = entry - (2 * atr.iloc[-1])
    target = entry + (3 * atr.iloc[-1])
    signal = "BUY" if score >= 4 else ("WATCH" if score >= 3 else "AVOID")

    return {
        "Signal": signal,
        "Score": score,
        "Entry": round(entry, 2),
        "StopLoss": round(stop_loss, 2),
        "Target": round(target, 2),
        "Reasons": ", ".join(reasons),
        "ADX": round(adx.iloc[-1], 2),
    }


def scan_universe(client, universe_df, interval="ONE_DAY", days=200, progress_cb=None):
    results = []
    total = len(universe_df)
    for i, (_, row) in enumerate(universe_df.iterrows()):
        try:
            token = row.get("token")
            if not token:
                continue
            df = client.get_historical(token, interval, days)
            if df.empty or len(df) < 50:
                continue
            sig = compute_swing_signals(df)
            if sig is None:
                continue
            sig["Symbol"] = row["Symbol"]
            sig["Sector"] = row.get("Sector", "Unknown")
            results.append(sig)
            if progress_cb:
                progress_cb((i + 1) / total)
            time.sleep(0.5)
        except Exception:
            continue
    return pd.DataFrame(results)
