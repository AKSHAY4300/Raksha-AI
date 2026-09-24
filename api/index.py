"""
Vercel Serverless Function Entrypoint
Routes all incoming web requests to the FastAPI application.
"""

import sys
from pathlib import Path

# Add project root to sys.path so app modules import cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.server import app

# Vercel serverless ASGI handler
handler = app
