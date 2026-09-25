"""
Vercel Serverless Function Entrypoint
Routes incoming web requests to the FastAPI application.
"""

import sys
import os
from pathlib import Path

# Add project root and app directory to sys.path so app modules import cleanly on Linux
ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "app"

for p in [str(ROOT_DIR), str(APP_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("VERCEL", "1")

# Direct top-level imports and assignments for Vercel AST analysis
from app.server import app

handler = app
application = app
