"""
Raksha AI - Supabase Cloud Database & Storage Adapter
Provides free tier cloud PostgreSQL & Realtime storage integration.
Fallback to local SQLite if Supabase credentials are not provided.
"""

import os
import json
import urllib.request
from typing import Dict, Any, List, Optional

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

class SupabaseAdapter:
    def __init__(self, url: str = "", key: str = ""):
        self.url = (url or SUPABASE_URL).rstrip("/")
        self.key = key or SUPABASE_KEY
        self.is_configured = bool(self.url and self.key)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "configured": False,
                "status": "Running in Local SQLite Mode (Cloud-Ready)",
                "message": "Set SUPABASE_URL and SUPABASE_KEY environment variables to enable direct Supabase cloud sync."
            }

        try:
            req = urllib.request.Request(
                f"{self.url}/rest/v1/incidents?select=id&limit=1",
                headers={
                    "apikey": self.key,
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return {
                    "configured": True,
                    "status": "Connected to Supabase Cloud",
                    "code": response.status
                }
        except Exception as e:
            return {
                "configured": True,
                "status": "Supabase Connection Error",
                "error": str(e)
            }

    def sync_incident_to_cloud(self, incident: Dict[str, Any]) -> bool:
        if not self.is_configured:
            return False

        try:
            payload = json.dumps(incident).encode('utf-8')
            req = urllib.request.Request(
                f"{self.url}/rest/v1/incidents",
                data=payload,
                headers={
                    "apikey": self.key,
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status in [200, 201]
        except Exception as e:
            print("Supabase cloud sync error:", e)
            return False

supabase_adapter = SupabaseAdapter()
