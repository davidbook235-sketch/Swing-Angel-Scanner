import pandas as pd
import requests
import streamlit as st


# Fallback token mapping — aap Angel One instrument master se full list le sakte hain
# https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json
FALLBACK_NIFTY250 = [
    {"Symbol": "RELIANCE", "token": "2885", "Sector": "NIFTY ENERGY"},
    {"Symbol": "TCS", "token": "11536", "Sector": "NIFTY IT"},
    {"Symbol": "HDFCBANK", "token": "1333", "Sector": "NIFTY BANK"},
    {"Symbol": "INFY", "token": "1594", "Sector": "NIFTY IT"},
    {"Symbol": "ICICIBANK", "token": "4963", "Sector": "NIFTY BANK"},
    {"Symbol": "HINDUNILVR", "token": "1394", "Sector": "NIFTY FMCG"},
    {"Symbol": "ITC", "token": "1660", "Sector": "NIFTY FMCG"},
    {"Symbol": "SBIN", "token": "3045", "Sector": "NIFTY PSU BANK"},
    {"Symbol": "BHARTIARTL", "token": "10604", "Sector": "NIFTY MEDIA"},
    {"Symbol": "LT", "token": "11483", "Sector": "NIFTY ENERGY"},
    {"Symbol": "KOTAKBANK", "token": "1922", "Sector": "NIFTY BANK"},
    {"Symbol": "AXISBANK", "token": "5900", "Sector": "NIFTY BANK"},
    {"Symbol": "MARUTI", "token": "10999", "Sector": "NIFTY AUTO"},
    {"Symbol": "SUNPHARMA", "token": "3351", "Sector": "NIFTY PHARMA"},
    {"Symbol": "TATAMOTORS", "token": "3456", "Sector": "NIFTY AUTO"},
    {"Symbol": "WIPRO", "token": "3787", "Sector": "NIFTY IT"},
    {"Symbol": "HCLTECH", "token": "7229", "Sector": "NIFTY IT"},
    {"Symbol": "ADANIENT", "token": "25", "Sector": "NIFTY ENERGY"},
    {"Symbol": "TITAN", "token": "3506", "Sector": "NIFTY FMCG"},
    {"Symbol": "ASIANPAINT", "token": "236", "Sector": "NIFTY FMCG"},
    # ... aap yahan 250 stocks add kar sakte hain
]


@st.cache_data(ttl=86400)
def load_nifty250():
    """
    Nifty 250 constituents load karein.
    Live fetch fail ho toh fallback use karein.
    """
    try:
        url = "https://www.niftyindices.com/IndexConstituent/ind_niftyLargeMidcap250list.csv"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        df = pd.read_csv(pd.io.common.StringIO(resp.text))
        df = df.rename(columns={"Company Name": "Company", "Industry": "Sector"})
        # Token mapping merge
        fallback_df = pd.DataFrame(FALLBACK_NIFTY250)
        df = df.merge(fallback_df, on="Symbol", how="left")
        return df[["Symbol", "Company", "Sector", "token"]].dropna(subset=["token"])
    except Exception:
        return pd.DataFrame(FALLBACK_NIFTY250)


def get_token(symbol):
    """Symbol se token nikalein"""
    df = pd.DataFrame(FALLBACK_NIFTY250)
    row = df[df["Symbol"] == symbol]
    return row.iloc[0]["token"] if not row.empty else None
