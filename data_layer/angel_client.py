import os
import time
import pandas as pd
import pyotp
import streamlit as st
from smartapi import SmartConnect
from datetime import datetime, timedelta


class AngelDataClient:
    def __init__(self):
        # Streamlit Cloud par st.secrets, local par os.getenv
        try:
            self.api_key = st.secrets["ANGEL_API_KEY"]
            self.client_id = st.secrets["ANGEL_CLIENT_ID"]
            self.mpin = st.secrets["ANGEL_MPIN"]
            self.totp_secret = st.secrets["ANGEL_TOTP_SECRET"]
        except Exception:
            self.api_key = os.getenv("ANGEL_API_KEY")
            self.client_id = os.getenv("ANGEL_CLIENT_ID")
            self.mpin = os.getenv("ANGEL_MPIN")
            self.totp_secret = os.getenv("ANGEL_TOTP_SECRET")

        self.obj = None
        self.session = None
        self.login()

    def login(self):
        try:
            totp = pyotp.TOTP(self.totp_secret).now()
            self.obj = SmartConnect(api_key=self.api_key)
            self.session = self.obj.generateSession(self.client_id, self.mpin, totp)
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def get_historical(self, symbol_token, interval="ONE_DAY", days=200):
        """interval: ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, ONE_DAY"""
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        params = {
            "exchange": "NSE",
            "symboltoken": str(symbol_token),
            "interval": interval,
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M"),
        }
        for attempt in range(3):
            try:
                data = self.obj.getCandleData(params)
                if not data or "data" not in data or data["data"] is None:
                    time.sleep(1)
                    continue
                df = pd.DataFrame(
                    data["data"],
                    columns=["timestamp", "open", "high", "low", "close", "volume"]
                )
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return df
            except Exception as e:
                time.sleep(2 ** attempt)
        return pd.DataFrame()

    def get_ltp(self, exchange, symbol, token):
        try:
            return self.obj.ltpData(exchange, symbol, token)
        except Exception:
            return None
