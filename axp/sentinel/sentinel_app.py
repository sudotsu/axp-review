"""
AxProtocol Sentinel API
-----------------------
FastAPI application for independent ledger verification.
Production-ready with proper error handling and logging.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from verify_ledger import verify_all

logger = logging.getLogger("axprotocol.sentinel")

# Configurable paths (defaults for Docker, override via env)
REPORTS_DIR = Path(os.getenv("AXP_REPORTS_DIR", "/audit/reports"))
LEDGER_DIR = os.getenv("AXP_LEDGER_DIR", "/audit/ledger")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AxProtocol Sentinel", version="1.0")


@app.get("/health")
def health() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Status and timestamp
    """
    return {
        "status": "ok",
        "ts": datetime.now(timezone.utc).isoformat(),
        "ledger_dir": LEDGER_DIR,
        "reports_dir": str(REPORTS_DIR)
    }


@app.get("/verify")
def verify() -> JSONResponse:
    """
    Verify ledger integrity and signatures.

    Returns:
        Verification report with details

    Raises:
        HTTPException: If verification fails critically
    """
    try:
        res = verify_all(ledger_dir=LEDGER_DIR)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = REPORTS_DIR / f"sentinel_{stamp}.json"

        try:
            with open(report_path, "w", encoding="utf8") as f:
                json.dump(res, f, indent=2)
            logger.info(f"Verification report written: {report_path}")
        except IOError as e:
            logger.error(f"Failed to write report: {e}")
            # Don't fail the request if report write fails

        return JSONResponse(res)
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.get("/reports")
def list_reports() -> Dict[str, List[str]]:
    """
    List recent verification reports.

    Returns:
        List of report filenames (last 30)
    """
    try:
        files = sorted([
            f.name for f in REPORTS_DIR.glob("*.json")
        ], reverse=True)[:30]
        return {"reports": files}
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        return {"reports": []}
