import json
import math
from datetime import datetime

import numpy as np
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from langchain_core.tools import tool


def sanitize_value(v):
    """Convert NaN/inf/numpy types to JSON-safe Python types."""
    if v is None:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(float(v), 4)
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, (np.ndarray,)):
        return [sanitize_value(x) for x in v.tolist()]
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    return v


def sanitize_dict(d: dict) -> dict:
    """Recursively sanitize all values in a dict."""
    return {k: sanitize_value(v) for k, v in d.items()}


@tool
def get_stock_technicals(ticker: str) -> str:
    """Fetch 1-year daily OHLCV data and compute technical indicators for a stock.
    Returns RSI(14), MACD(12,26,9), Bollinger Bands(20,2), SMA(20/50/200),
    volume ratio, and recent price changes.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y", interval="1d")

        if df.empty or len(df) < 50:
            return json.dumps({"error": f"Insufficient data for {ticker}"})

        # Compute indicators
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest

        close = float(latest["Close"])
        sma_20 = latest.get("SMA_20")
        sma_50 = latest.get("SMA_50")
        sma_200 = latest.get("SMA_200")

        # Volume ratio (current vs 20-day average)
        vol_20_avg = df["Volume"].tail(20).mean()
        volume_ratio = float(latest["Volume"]) / vol_20_avg if vol_20_avg > 0 else 1.0

        # Price changes
        price_1d = ((close - float(prev["Close"])) / float(prev["Close"])) * 100 if float(prev["Close"]) > 0 else 0
        price_5d = ((close - float(df.iloc[-5]["Close"])) / float(df.iloc[-5]["Close"])) * 100 if len(df) >= 5 else 0
        price_20d = ((close - float(df.iloc[-20]["Close"])) / float(df.iloc[-20]["Close"])) * 100 if len(df) >= 20 else 0

        # Bollinger Band width
        bb_upper = latest.get("BBU_20_2.0")
        bb_lower = latest.get("BBL_20_2.0")
        bb_mid = latest.get("BBM_20_2.0")
        bb_width = (float(bb_upper) - float(bb_lower)) / float(bb_mid) if bb_mid and float(bb_mid) > 0 else None

        result = sanitize_dict({
            "ticker": ticker,
            "date": latest.name.isoformat() if hasattr(latest.name, "isoformat") else str(latest.name),
            "close": close,
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "volume": int(latest["Volume"]),
            "rsi_14": latest.get("RSI_14"),
            "macd": latest.get("MACD_12_26_9"),
            "macd_signal": latest.get("MACDs_12_26_9"),
            "macd_histogram": latest.get("MACDh_12_26_9"),
            "bb_upper": bb_upper,
            "bb_mid": bb_mid,
            "bb_lower": bb_lower,
            "bb_width": bb_width,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "volume_ratio": volume_ratio,
            "price_change_1d": price_1d,
            "price_change_5d": price_5d,
            "price_change_20d": price_20d,
            "sma_20_distance_pct": ((close - float(sma_20)) / float(sma_20) * 100) if sma_20 and not (isinstance(sma_20, float) and math.isnan(sma_20)) else None,
            "sma_50_distance_pct": ((close - float(sma_50)) / float(sma_50) * 100) if sma_50 and not (isinstance(sma_50, float) and math.isnan(sma_50)) else None,
            "sma_200_distance_pct": ((close - float(sma_200)) / float(sma_200) * 100) if sma_200 and not (isinstance(sma_200, float) and math.isnan(sma_200)) else None,
            "above_sma_20": close > float(sma_20) if sma_20 and not (isinstance(sma_20, float) and math.isnan(sma_20)) else None,
            "above_sma_50": close > float(sma_50) if sma_50 and not (isinstance(sma_50, float) and math.isnan(sma_50)) else None,
            "above_sma_200": close > float(sma_200) if sma_200 and not (isinstance(sma_200, float) and math.isnan(sma_200)) else None,
        })

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": f"Failed to get technicals for {ticker}: {str(e)}"})
