"""Phase A: Rule-based screener that filters stocks by technical signals.

Uses yf.download() for batch downloading to handle 500+ tickers efficiently.
"""

import logging
import math
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import pandas_ta as ta
import yfinance as yf

from config import ALL_TICKERS, SCREENING_RULES
from tools.technicals import sanitize_value, sanitize_dict

logger = logging.getLogger(__name__)

# Number of tickers per batch for yf.download()
BATCH_SIZE = 50


def _compute_signals_from_df(ticker: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Compute technical signals for a single ticker from pre-fetched OHLCV data."""
    try:
        if df.empty or len(df) < 50:
            return {"ticker": ticker, "error": "insufficient data", "signals": [], "signal_count": 0}

        df = df.copy()
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)

        latest = df.iloc[-1]
        close = float(latest["Close"])
        signals = []
        direction_hints = []

        # ── RSI ───────────────────────────────────────────────────────────
        rsi = latest.get("RSI_14")
        if rsi is not None and not math.isnan(float(rsi)):
            rsi = float(rsi)
            if rsi <= SCREENING_RULES.rsi_oversold:
                signals.append(f"RSI oversold ({rsi:.1f})")
                direction_hints.append("bullish")
            elif rsi >= SCREENING_RULES.rsi_overbought:
                signals.append(f"RSI overbought ({rsi:.1f})")
                direction_hints.append("bearish")

        # ── MACD Histogram ────────────────────────────────────────────────
        macd_h = latest.get("MACDh_12_26_9")
        if macd_h is not None and not math.isnan(float(macd_h)):
            macd_h = float(macd_h)
            prev_macd_h = df.iloc[-2].get("MACDh_12_26_9") if len(df) >= 2 else None
            if prev_macd_h is not None and not math.isnan(float(prev_macd_h)):
                prev_macd_h = float(prev_macd_h)
                if macd_h > prev_macd_h and macd_h > SCREENING_RULES.macd_histogram_threshold:
                    signals.append("MACD histogram rising (bullish momentum)")
                    direction_hints.append("bullish")
                elif macd_h < prev_macd_h and macd_h < -SCREENING_RULES.macd_histogram_threshold:
                    signals.append("MACD histogram falling (bearish momentum)")
                    direction_hints.append("bearish")

        # ── Bollinger Bands ───────────────────────────────────────────────
        bb_upper = latest.get("BBU_20_2.0")
        bb_lower = latest.get("BBL_20_2.0")
        bb_mid = latest.get("BBM_20_2.0")

        bb_valid = all(
            v is not None and not math.isnan(float(v))
            for v in [bb_upper, bb_lower, bb_mid]
        )
        if bb_valid:
            bb_upper, bb_lower, bb_mid = float(bb_upper), float(bb_lower), float(bb_mid)
            bb_width = (bb_upper - bb_lower) / bb_mid if bb_mid > 0 else 0

            if bb_width < SCREENING_RULES.bb_squeeze_threshold:
                signals.append(f"BB squeeze (width={bb_width:.3f})")
                direction_hints.append("neutral")
            if close <= bb_lower:
                signals.append("Price at lower Bollinger Band")
                direction_hints.append("bullish")
            elif close >= bb_upper:
                signals.append("Price at upper Bollinger Band")
                direction_hints.append("bearish")

        # ── SMA Proximity ─────────────────────────────────────────────────
        for sma_col, label in [("SMA_20", "20"), ("SMA_50", "50"), ("SMA_200", "200")]:
            sma_val = latest.get(sma_col)
            if sma_val is not None and not math.isnan(float(sma_val)):
                sma_val = float(sma_val)
                dist_pct = abs((close - sma_val) / sma_val) * 100
                if dist_pct <= SCREENING_RULES.sma_proximity_pct:
                    if close > sma_val:
                        signals.append(f"Testing SMA{label} support from above ({dist_pct:.1f}%)")
                        direction_hints.append("bullish")
                    else:
                        signals.append(f"Approaching SMA{label} resistance from below ({dist_pct:.1f}%)")
                        direction_hints.append("bullish")

        # ── Volume Surge ──────────────────────────────────────────────────
        vol_20_avg = df["Volume"].tail(20).mean()
        if vol_20_avg > 0:
            vol_ratio = float(latest["Volume"]) / vol_20_avg
            if vol_ratio >= SCREENING_RULES.volume_surge_multiplier:
                signals.append(f"Volume surge ({vol_ratio:.1f}x average)")
                direction_hints.append("neutral")

        # Determine overall direction
        bullish = direction_hints.count("bullish")
        bearish = direction_hints.count("bearish")
        if bullish > bearish:
            direction = "bullish"
        elif bearish > bullish:
            direction = "bearish"
        else:
            direction = "neutral"

        return sanitize_dict({
            "ticker": ticker,
            "close": close,
            "signals": signals,
            "signal_count": len(signals),
            "direction": direction,
            "rsi": latest.get("RSI_14"),
            "macd_histogram": latest.get("MACDh_12_26_9"),
            "bb_width": (float(latest.get("BBU_20_2.0", 0)) - float(latest.get("BBL_20_2.0", 0)))
            / float(latest.get("BBM_20_2.0", 1))
            if bb_valid and float(latest.get("BBM_20_2.0", 0)) > 0
            else None,
        })

    except Exception as e:
        return {"ticker": ticker, "error": str(e), "signals": [], "signal_count": 0}


def _download_batch(tickers: List[str]) -> Dict[str, pd.DataFrame]:
    """Download 1-year daily data for a batch of tickers using yf.download()."""
    result = {}
    if not tickers:
        return result

    try:
        data = yf.download(
            tickers,
            period="1y",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False,
        )

        if data.empty:
            return result

        if len(tickers) == 1:
            # yf.download returns flat columns for single ticker
            result[tickers[0]] = data.dropna(how="all")
        else:
            for ticker in tickers:
                try:
                    ticker_df = data[ticker].dropna(how="all")
                    if not ticker_df.empty:
                        result[ticker] = ticker_df
                except (KeyError, Exception):
                    continue

    except Exception as e:
        logger.warning(f"Batch download failed: {e}")

    return result


def run_screener() -> Dict[str, Any]:
    """Run Phase A screening on all watchlist tickers.

    Downloads data in batches of BATCH_SIZE for efficiency,
    then computes signals per ticker.
    """
    passed = []
    failed = []
    total = len(ALL_TICKERS)

    # Download in batches
    all_data: Dict[str, pd.DataFrame] = {}
    for i in range(0, total, BATCH_SIZE):
        batch = ALL_TICKERS[i : i + BATCH_SIZE]
        logger.info(f"Downloading batch {i // BATCH_SIZE + 1} ({len(batch)} tickers)...")
        batch_data = _download_batch(batch)
        all_data.update(batch_data)

    logger.info(f"Downloaded data for {len(all_data)}/{total} tickers")

    # Compute signals
    for ticker in ALL_TICKERS:
        df = all_data.get(ticker)
        if df is None or df.empty:
            failed.append({"ticker": ticker, "error": "no data", "signals": [], "signal_count": 0})
            continue

        result = _compute_signals_from_df(ticker, df)
        if result.get("signal_count", 0) >= SCREENING_RULES.min_signals_to_pass:
            passed.append(result)
        else:
            failed.append(result)

    passed.sort(key=lambda x: x.get("signal_count", 0), reverse=True)

    return {
        "total_universe": total,
        "passed_count": len(passed),
        "failed_count": len(failed),
        "passed": passed,
        "failed": failed,
    }
