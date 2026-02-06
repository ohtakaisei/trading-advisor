import json
import logging

import yfinance as yf
from langchain_core.tools import tool

from config import ALL_TICKERS, SCREENING_RULES

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


@tool
def scan_unusual_volume() -> str:
    """Scan all watchlist stocks for unusual volume (> 2x 20-day average).
    Returns a list of tickers with volume significantly above their recent average.
    """
    try:
        unusual = []

        # Batch download 1-month data
        for i in range(0, len(ALL_TICKERS), BATCH_SIZE):
            batch = ALL_TICKERS[i : i + BATCH_SIZE]
            try:
                data = yf.download(
                    batch,
                    period="1mo",
                    interval="1d",
                    group_by="ticker",
                    threads=True,
                    progress=False,
                )
                if data.empty:
                    continue

                for ticker in batch:
                    try:
                        if len(batch) == 1:
                            hist = data.dropna(how="all")
                        else:
                            hist = data[ticker].dropna(how="all")

                        if hist.empty or len(hist) < 5:
                            continue

                        latest_vol = float(hist["Volume"].iloc[-1])
                        avg_vol = float(hist["Volume"].tail(20).mean())
                        if avg_vol <= 0:
                            continue

                        ratio = latest_vol / avg_vol
                        if ratio >= SCREENING_RULES.unusual_volume_multiplier:
                            close = float(hist["Close"].iloc[-1])
                            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else close
                            price_change = ((close - prev_close) / prev_close) * 100 if prev_close > 0 else 0

                            unusual.append({
                                "ticker": ticker,
                                "volume": int(latest_vol),
                                "avg_volume_20d": int(avg_vol),
                                "volume_ratio": round(ratio, 2),
                                "close": round(close, 2),
                                "price_change_pct": round(price_change, 2),
                            })
                    except (KeyError, Exception):
                        continue
            except Exception:
                continue

        unusual.sort(key=lambda x: x["volume_ratio"], reverse=True)

        return json.dumps({
            "unusual_volume_stocks": unusual,
            "count": len(unusual),
            "threshold": f"{SCREENING_RULES.unusual_volume_multiplier}x 20-day average",
        })

    except Exception as e:
        return json.dumps({"error": f"Volume scan failed: {str(e)}"})
