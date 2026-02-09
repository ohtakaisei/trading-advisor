"""FastAPI server for the trading advisor."""

import json
import logging
import os
import threading
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent import run_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Advisor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Concurrency guard - only one scan at a time
_scan_lock = threading.Lock()


@app.post("/api/scan")
def run_scan():
    """Run the full analysis pipeline and save the report."""
    if not _scan_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A scan is already in progress")

    try:
        logger.info("Starting full scan pipeline")
        report = run_analysis()

        # Save report
        today = date.today().isoformat()
        report["date"] = today
        report_path = REPORTS_DIR / f"{today}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Report saved to {report_path}")
        return report

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        _scan_lock.release()


@app.get("/api/reports")
def list_reports():
    """List all saved reports with summary metadata, newest first."""
    reports = []
    for f in sorted(REPORTS_DIR.glob("*.json"), reverse=True):
        try:
            with open(f) as fh:
                data = json.load(fh)
            reports.append({
                "date": f.stem,
                "candidates": len(data.get("candidates", [])),
                "watchlist": len(data.get("watchlist", [])),
                "trend": data.get("market_overview", {}).get("trend", "unknown"),
            })
        except Exception:
            continue

    return reports


@app.get("/api/reports/{report_date}")
def get_report(report_date: str):
    """Return a specific report by date."""
    report_path = REPORTS_DIR / f"{report_date}.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    with open(report_path) as f:
        return json.load(f)


# ---------- Static file serving (production) ----------
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA for any non-API route."""
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")
