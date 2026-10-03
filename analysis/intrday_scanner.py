import pandas as pd
import numpy as np
from ta.volume import VolumeWeightedAveragePrice
from ta.trend import EMAIndicator


def compute_intraday_signals(df_5min):
    if len(df_5min) < 20:
        return None

    df_5min = df_5min.copy()
    df_5min.set_index("timestamp", inplace=True)

    close = df_5min["close"]
    high = df_5min["high"]
    low = df_5min["low"]
    volume = df_5min["volume"]

    try:
        vwap = VolumeWeightedAveragePrice(high, low, close, volume).volume_weighted_average_price()
    except Exception:
        vwap = close.rolling(20).mean()

    orb_data = df_5min.between_time("09:15", "09:30")
    orb_high = orb_data["high"].max() if not orb_data.empty else high.max()
    orb_low = orb_data["low"].min() if not orb_data.empty else low.min()

    ema9 = EMAIndicator(close, window=9).ema_indicator()
    ema21 = EMAIndicator(close, window=21).ema_indicator()

    current = close.iloc[-1]
    signals = []

    if not pd.isna(vwap.iloc[-1]) and current > vwap.iloc[-1]:
        signals.append("Price > VWAP")
    if current > orb_high:
        signals.append("ORB Breakout")
    if ema9.iloc[-1] > ema21.iloc[-1]:
        signals.append("EMA9 > EMA21")

    atr_val = (high - low).rolling(14).mean().iloc[-1]
    if pd.isna(atr_val):
        atr_val = current * 0.01

    return {
        "Intraday_Signal": "BUY" if len(signals) >= 2 else "WAIT",
        "Entry": round(current, 2),
        "StopLoss": round(current - atr_val, 2),
        "Target": round(current + (1.5 * atr_val), 2),
        "VWAP": round(vwap.iloc[-1], 2) if not pd.isna(vwap.iloc[-1]) else 0,
        "ORB_High": round(orb_high, 2),
        "Reasons": ", ".join(signals),
    }
