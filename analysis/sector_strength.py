import pandas as pd
import numpy as np


SECTOR_INDICES = {
    "NIFTY BANK": "NIFTY BANK",
    "NIFTY IT": "NIFTY IT",
    "NIFTY PHARMA": "NIFTY PHARMA",
    "NIFTY AUTO": "NIFTY AUTO",
    "NIFTY METAL": "NIFTY METAL",
    "NIFTY FMCG": "NIFTY FMCG",
    "NIFTY REALTY": "NIFTY REALTY",
    "NIFTY MEDIA": "NIFTY MEDIA",
    "NIFTY ENERGY": "NIFTY ENERGY",
    "NIFTY PSU BANK": "NIFTY PSU BANK",
}


def compute_sector_strength(client, benchmark_df, sector_token_map=None):
    """
    Simplified version — sector data benchmark ke saath proxy.
    Aap yahan actual sector indices fetch kar sakte hain.
    """
    if benchmark_df.empty:
        return pd.DataFrame()

    bench_close = benchmark_df.set_index("timestamp")["close"]
    results = []

    # Demo: har sector ke liye random strength (aap actual data fetch karein)
    # Real implementation: sector index tokens Angel One se fetch karein
    for sector_name in SECTOR_INDICES.keys():
        try:
            # Placeholder metrics
            ret_1m = np.random.uniform(-10, 15)
            ret_3m = np.random.uniform(-15, 25)
            rs_ratio = 100 + (ret_1m / 2)
            rs_momentum = 100 + (ret_3m / 4)

            if rs_ratio > 100 and rs_momentum > 100:
                quadrant = "LEADING"
            elif rs_ratio > 100 and rs_momentum < 100:
                quadrant = "WEAKENING"
            elif rs_ratio < 100 and rs_momentum < 100:
                quadrant = "LAGGING"
            else:
                quadrant = "IMPROVING"

            results.append({
                "Sector": sector_name,
                "1M_Return_%": round(ret_1m, 2),
                "3M_Return_%": round(ret_3m, 2),
                "RS_Ratio": round(rs_ratio, 2),
                "RS_Momentum": round(rs_momentum, 2),
                "Quadrant": quadrant,
                "Strength_Score": round((rs_ratio + rs_momentum) / 2, 2),
            })
        except Exception:
            continue

    return pd.DataFrame(results).sort_values("Strength_Score", ascending=False)


def get_stock_sector_boost(stock_sector, sector_df):
    if sector_df.empty:
        return 0
    row = sector_df[sector_df["Sector"] == stock_sector]
    if row.empty:
        return 0
    strength = row.iloc[0]["Strength_Score"]
    if strength > 105:
        return 1
    elif strength < 95:
        return -1
    return 0
