import json
from datetime import datetime

import yfinance as yf
from langchain_core.tools import tool


@tool
def get_earnings_calendar(ticker: str) -> str:
    """Get the next earnings date for a stock and whether earnings are imminent (within 5 trading days).

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')
    """
    try:
        stock = yf.Ticker(ticker)
        next_earnings = None

        # Strategy 1: Try .calendar
        try:
            cal = stock.calendar
            if cal is not None:
                if isinstance(cal, dict):
                    ed = cal.get("Earnings Date")
                    if ed:
                        if isinstance(ed, list) and len(ed) > 0:
                            next_earnings = ed[0]
                        elif hasattr(ed, "isoformat"):
                            next_earnings = ed
                elif hasattr(cal, "columns"):
                    if "Earnings Date" in cal.columns:
                        next_earnings = cal["Earnings Date"].iloc[0]
                    elif len(cal) > 0:
                        next_earnings = cal.iloc[0, 0]
        except Exception:
            pass

        # Strategy 2: Fallback to get_earnings_dates
        if next_earnings is None:
            try:
                dates = stock.get_earnings_dates(limit=4)
                if dates is not None and not dates.empty:
                    now = datetime.now()
                    future_dates = [d for d in dates.index if d.to_pydatetime().replace(tzinfo=None) > now]
                    if future_dates:
                        next_earnings = min(future_dates)
            except Exception:
                pass

        if next_earnings is None:
            return json.dumps({
                "ticker": ticker,
                "next_earnings_date": None,
                "days_to_earnings": None,
                "earnings_imminent": False,
                "note": "Could not determine next earnings date",
            })

        # Calculate days to earnings
        if hasattr(next_earnings, "to_pydatetime"):
            earnings_dt = next_earnings.to_pydatetime().replace(tzinfo=None)
        elif hasattr(next_earnings, "replace"):
            earnings_dt = next_earnings.replace(tzinfo=None) if hasattr(next_earnings, "tzinfo") else next_earnings
        else:
            earnings_dt = datetime.fromisoformat(str(next_earnings))

        days_to = (earnings_dt - datetime.now()).days

        return json.dumps({
            "ticker": ticker,
            "next_earnings_date": earnings_dt.strftime("%Y-%m-%d"),
            "days_to_earnings": days_to,
            "earnings_imminent": days_to <= 5,
        })

    except Exception as e:
        return json.dumps({
            "ticker": ticker,
            "error": f"Failed to get earnings for {ticker}: {str(e)}",
            "next_earnings_date": None,
            "days_to_earnings": None,
            "earnings_imminent": False,
        })
