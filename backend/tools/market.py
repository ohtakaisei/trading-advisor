import json
import math

import numpy as np
import yfinance as yf
from langchain_core.tools import tool

from config import SECTOR_ETFS


def _safe_float(v):
    if v is None:
        return None
    f = float(v)
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, 4)


def _get_change(ticker_str: str, period: str = "5d") -> dict:
    """Get price change for a ticker over a period."""
    try:
        t = yf.Ticker(ticker_str)
        hist = t.history(period=period)
        if hist.empty or len(hist) < 2:
            return {"ticker": ticker_str, "change_pct": None, "close": None}

        close = float(hist["Close"].iloc[-1])
        open_price = float(hist["Close"].iloc[0])
        change_pct = ((close - open_price) / open_price) * 100 if open_price > 0 else 0

        return {
            "ticker": ticker_str,
            "close": _safe_float(close),
            "change_pct": _safe_float(change_pct),
        }
    except Exception:
        return {"ticker": ticker_str, "change_pct": None, "close": None}


@tool
def get_market_overview() -> str:
    """Get a broad market overview including SPY, QQQ, VIX, 10Y yield, USD index,
    and all 11 sector ETF performance (1-day and 5-day changes).
    """
    try:
        # Major indices
        spy = _get_change("SPY", "5d")
        qqq = _get_change("QQQ", "5d")

        # VIX
        try:
            vix_data = yf.Ticker("^VIX").history(period="5d")
            vix_close = _safe_float(vix_data["Close"].iloc[-1]) if not vix_data.empty else None
        except Exception:
            vix_close = None

        # 10Y yield
        try:
            tnx_data = yf.Ticker("^TNX").history(period="5d")
            tnx_close = _safe_float(tnx_data["Close"].iloc[-1]) if not tnx_data.empty else None
        except Exception:
            tnx_close = None

        # Dollar index
        try:
            dx_data = yf.Ticker("DX-Y.NYB").history(period="5d")
            dx_close = _safe_float(dx_data["Close"].iloc[-1]) if not dx_data.empty else None
        except Exception:
            dx_close = None

        # Sector ETFs
        sectors = []
        for etf in SECTOR_ETFS:
            d1 = _get_change(etf, "2d")  # ~1 day
            d5 = _get_change(etf, "5d")
            sectors.append({
                "ticker": etf,
                "close": d5.get("close"),
                "change_1d": d1.get("change_pct"),
                "change_5d": d5.get("change_pct"),
            })

        # Determine overall trend
        spy_chg = spy.get("change_pct") or 0
        if spy_chg > 1:
            trend = "bullish"
        elif spy_chg < -1:
            trend = "bearish"
        else:
            trend = "neutral"

        result = {
            "spy": spy,
            "qqq": qqq,
            "vix": vix_close,
            "treasury_10y": tnx_close,
            "usd_index": dx_close,
            "sectors": sectors,
            "market_trend": trend,
        }

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": f"Failed to get market overview: {str(e)}"})
