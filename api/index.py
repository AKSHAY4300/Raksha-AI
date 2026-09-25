"""
Vercel Serverless Function Entrypoint
Routes incoming web requests to the FastAPI application.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path so app modules import cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure VERCEL environment is recognized
os.environ.setdefault("VERCEL", "1")

try:
    from app.server import app
    handler = app
except Exception as e:
    import traceback
    err_msg = str(e)
    tb_lines = traceback.format_exc().splitlines()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI(title="Raksha AI Serverless Diagnostic")
    handler = app

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def serverless_error_handler(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Serverless Startup Failure",
                "detail": err_msg,
                "traceback": tb_lines[-8:]
            }
        )
