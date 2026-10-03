import pandas as pd
from ta.trend import ADXIndicator


def get_nifty_regime(nifty_df, adx_threshold=25):
    if len(nifty_df) < 50:
        return {"regime": "UNKNOWN", "adx": 0, "advice": "Insufficient data", "is_trending": False}

    adx = ADXIndicator(
        nifty_df["high"], nifty_df["low"], nifty_df["close"], window=14
    ).adx()

    current_adx = adx.iloc[-1]
    ema20 = nifty_df["close"].ewm(span=20).mean().iloc[-1]
    ema50 = nifty_df["close"].ewm(span=50).mean().iloc[-1]

    if current_adx > adx_threshold:
        if ema20 > ema50:
            regime = "TRENDING_UP"
            advice = "Swing buys allowed"
        else:
            regime = "TRENDING_DOWN"
            advice = "Avoid longs"
    else:
        regime = "RANGING"
        advice = "Mean reversion, tighter stops"

    return {
        "regime": regime,
        "adx": round(current_adx, 2),
        "advice": advice,
        "is_trending": current_adx > adx_threshold,
    }


def apply_regime_filter(signals_df, regime_info, enabled=True):
    if not enabled or signals_df.empty:
        return signals_df

    if regime_info["regime"] == "TRENDING_DOWN":
        return signals_df[signals_df["Score"] >= 4]
    elif regime_info["regime"] == "RANGING":
        return signals_df[signals_df["Score"] >= 4]
    return signals_df
