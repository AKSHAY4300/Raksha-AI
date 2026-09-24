"""
Comprehensive Test Suite for Raksha AI / RoadVision AI Platform
Tests Cryptography (AES-256-GCM), Geofencing, Database CRUD, Telemetry,
Inference Simulator, Supabase Cloud Adapter, and All FastAPI Endpoints.
"""

import sys
import unittest
import json
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from starlette.testclient import TestClient
from app.server import app
from app.crypto_utils import crypto_engine
from app.database import db, haversine_distance
from app.supabase_client import SupabaseAdapter


class TestVisionAIFullSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -------------------------------------------------------------
    # 1. Cryptography Unit Tests (AES-256-GCM)
    # -------------------------------------------------------------
    def test_01_crypto_engine_roundtrip(self):
        """Test that AES-256-GCM encryption & decryption restores the exact payload."""
        sample_data = {
            "bus_id": "BUS-999",
            "hazard_type": "accident_collision",
            "lat": 13.0827,
            "lng": 80.2707,
            "category": "POLICE",
            "severity": "CRITICAL",
            "speed_kmh": 45.5,
            "title": "Unit Test Accident Alert"
        }
        encrypted = crypto_engine.encrypt_gcm(sample_data)
        self.assertIn("ciphertext", encrypted)
        self.assertIn("iv", encrypted)
        self.assertIn("tag", encrypted)
        self.assertIn("algorithm", encrypted)
        self.assertEqual(encrypted["algorithm"], "AES-256-GCM")

        # Decrypt and verify
        decrypted = crypto_engine.decrypt_gcm(encrypted)
        self.assertEqual(decrypted["bus_id"], "BUS-999")
        self.assertEqual(decrypted["category"], "POLICE")
        self.assertEqual(decrypted["lat"], 13.0827)

    def test_02_crypto_engine_tamper_detection(self):
        """Test that tampering with ciphertext fails GCM authentication."""
        sample_data = {"test": "value"}
        encrypted = crypto_engine.encrypt_gcm(sample_data)
        
        # Tamper with the ciphertext
        corrupted_packet = dict(encrypted)
        ct = corrupted_packet["ciphertext"]
        corrupted_packet["ciphertext"] = ("aa" if not ct.startswith("aa") else "bb") + ct[2:]

        with self.assertRaises(Exception):
            crypto_engine.decrypt_gcm(corrupted_packet)

    # -------------------------------------------------------------
    # 2. Spatial & Database Unit Tests
    # -------------------------------------------------------------
    def test_03_haversine_distance(self):
        """Test spherical distance calculation accuracy between coordinates."""
        # Distance between Chennai Central (13.0827, 80.2707) and Marina Beach (13.0499, 80.2824)
        dist = haversine_distance(13.0827, 80.2707, 13.0499, 80.2824)
        # Should be approx 3.8km - 4.2km (3800m - 4200m)
        self.assertTrue(3500 < dist < 4500, f"Distance calculated was {dist}m")

    def test_04_database_incident_lifecycle_and_geofencing(self):
        """Test creating an incident, verifying geofence, and updating to REPAIRED/CLEARED."""
        test_incident_data = {
            "category": "PWD",
            "hazard_type": "pothole",
            "title": "Automated Test Pothole",
            "description": "Test defect created by test suite",
            "severity": "HIGH",
            "lat": 13.0850,
            "lng": 80.2750,
            "address": "Test Road Lane 1",
            "geofence_radius": 120.0,
            "status": "ACTIVE"
        }
        created = db.create_incident(test_incident_data)
        incident_id = created["id"]
        self.assertIsNotNone(incident_id)

        # Verify it appears in active geofences
        active_geos = db.get_active_geofences()
        matching = [g for g in active_geos if g["id"] == incident_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["status"], "ACTIVE")

        # Update status to ACKNOWLEDGED
        ack = db.update_incident_status(incident_id, "ACKNOWLEDGED", actor_name="Test Dispatcher")
        self.assertIsNotNone(ack)
        self.assertEqual(ack["status"], "ACKNOWLEDGED")

        # Should still be active geofence
        active_geos = db.get_active_geofences()
        self.assertTrue(any(g["id"] == incident_id for g in active_geos))

        # Mark REPAIRED
        rep = db.update_incident_status(incident_id, "REPAIRED", actor_name="Test Repair Unit")
        self.assertIsNotNone(rep)
        self.assertEqual(rep["status"], "REPAIRED")

        # MUST be removed from active geofences
        active_geos_after = db.get_active_geofences()
        self.assertFalse(any(g["id"] == incident_id for g in active_geos_after))

    def test_05_bus_proximity_alert_calculation(self):
        """Test proximity alerts trigger when bus is near hazard, and not when far."""
        # Create an active incident
        hazard = db.create_incident({
            "category": "POLICE",
            "hazard_type": "accident_collision",
            "title": "Proximity Test Incident",
            "severity": "CRITICAL",
            "lat": 13.1000,
            "lng": 80.2000,
            "geofence_radius": 150.0,
            "status": "ACTIVE"
        })

        # Bus directly at the hazard location (0m away) -> should trigger alert
        alerts_near = db.check_proximity_alerts(13.1000, 80.2000, warning_buffer=50.0)
        self.assertTrue(len(alerts_near) > 0)
        self.assertTrue(any(a["incident_id"] == hazard["id"] for a in alerts_near))

        # Bus far away (10km north) -> should not trigger alert for this hazard
        alerts_far = db.check_proximity_alerts(13.2000, 80.2000, warning_buffer=50.0)
        self.assertFalse(any(a["incident_id"] == hazard["id"] for a in alerts_far))

        # Clean up by clearing the incident
        db.update_incident_status(hazard["id"], "CLEARED")

    # -------------------------------------------------------------
    # 3. Supabase Cloud Adapter Unit Tests
    # -------------------------------------------------------------
    def test_06_supabase_adapter_unconfigured(self):
        """Test that Supabase adapter safely falls back to local SQLite when unconfigured."""
        adapter = SupabaseAdapter(url="", key="")
        self.assertFalse(adapter.is_configured)
        status = adapter.test_connection()
        self.assertFalse(status["configured"])
        self.assertIn("Local SQLite", status["status"])

    # -------------------------------------------------------------
    # 4. HTTP / API Endpoint Integration Tests
    # -------------------------------------------------------------
    def test_07_portal_html_endpoints(self):
        """Test that all frontend portal views return 200 OK and HTML."""
        routes = ["/", "/police-hq", "/pwd-admin", "/driver-madt", "/bus-edge", "/cloud-deploy"]
        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} returned status {resp.status_code}")
            self.assertIn("text/html", resp.headers.get("content-type", ""))
            self.assertIn("<!DOCTYPE html>", resp.text)

    def test_08_static_assets_serving(self):
        """Test that static CSS and JS are served properly."""
        css_resp = self.client.get("/static/app.css")
        self.assertEqual(css_resp.status_code, 200)
        self.assertTrue(len(css_resp.text) > 500)

        js_resp = self.client.get("/static/app.js")
        self.assertEqual(js_resp.status_code, 200)
        self.assertTrue(len(js_resp.text) > 500)

    def test_09_api_status_and_kpi(self):
        """Test system status and KPI endpoints."""
        status_resp = self.client.get("/api/status")
        self.assertEqual(status_resp.status_code, 200)
        data = status_resp.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("encryption", data)
        self.assertTrue(data["encryption"]["active"])
        self.assertIn("cloud_storage", data)
        self.assertIn("kpi", data)

        kpi_resp = self.client.get("/api/kpi-summary")
        self.assertEqual(kpi_resp.status_code, 200)
        kpi = kpi_resp.json()
        self.assertIn("police", kpi)
        self.assertIn("pwd", kpi)
        self.assertIn("total_active_geofences", kpi)

    def test_10_police_hq_endpoints(self):
        """Test Police HQ incident fetching, acknowledging, and clearing."""
        # Fetch incidents
        resp = self.client.get("/api/police-hq/incidents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["authority"], "POLICE_HEADQUARTERS")
        self.assertIsInstance(data["incidents"], list)

        # Create a new police incident to test action flows
        new_inc = db.create_incident({
            "category": "POLICE",
            "hazard_type": "traffic_congestion",
            "title": "Police Test Gridlock",
            "severity": "HIGH",
            "lat": 13.0800,
            "lng": 80.2600,
            "status": "ACTIVE"
        })
        inc_id = new_inc["id"]

        # Acknowledge
        ack_resp = self.client.patch(
            f"/api/police-hq/incidents/{inc_id}/acknowledge",
            json={"actor_name": "Sergeant 42", "notes": "Patrol van dispatched"}
        )
        self.assertEqual(ack_resp.status_code, 200)
        self.assertEqual(ack_resp.json()["incident"]["status"], "ACKNOWLEDGED")

        # Clear
        clear_resp = self.client.patch(
            f"/api/police-hq/incidents/{inc_id}/clear",
            json={"actor_name": "Sergeant 42", "notes": "Congestion dispersed"}
        )
        self.assertEqual(clear_resp.status_code, 200)
        self.assertEqual(clear_resp.json()["incident"]["status"], "REPAIRED")

    def test_11_pwd_endpoints(self):
        """Test PWD incident fetching, acknowledging, and repairing."""
        resp = self.client.get("/api/pwd/incidents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["authority"], "PUBLIC_WORKS_DEPARTMENT")
        self.assertIsInstance(data["incidents"], list)

        new_inc = db.create_incident({
            "category": "PWD",
            "hazard_type": "pothole",
            "title": "PWD Test Crater",
            "severity": "CRITICAL",
            "lat": 13.0700,
            "lng": 80.2500,
            "status": "ACTIVE"
        })
        inc_id = new_inc["id"]

        # Acknowledge
        ack_resp = self.client.patch(
            f"/api/pwd/incidents/{inc_id}/acknowledge",
            json={"actor_name": "PWD Engineer", "notes": "Material ordered"}
        )
        self.assertEqual(ack_resp.status_code, 200)
        self.assertEqual(ack_resp.json()["incident"]["status"], "ACKNOWLEDGED")

        # Repair
        rep_resp = self.client.patch(
            f"/api/pwd/incidents/{inc_id}/repair",
            json={"actor_name": "PWD Road Crew", "notes": "Patching finished"}
        )
        self.assertEqual(rep_resp.status_code, 200)
        self.assertEqual(rep_resp.json()["incident"]["status"], "REPAIRED")

    def test_12_geofences_active_endpoint(self):
        """Test active geofences API."""
        resp = self.client.get("/api/geofences/active")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_active", data)
        self.assertIn("geofences", data)

    def test_13_bus_telemetry_and_proximity_endpoint(self):
        """Test Bus telemetry update and proximity query."""
        post_resp = self.client.post("/api/bus/telemetry", json={
            "bus_id": "TEST-BUS-01",
            "lat": 13.0827,
            "lng": 80.2707,
            "speed_kmh": 40.0,
            "heading": 180.0,
            "route_id": "ROUTE-99",
            "route_name": "Express Corridor"
        })
        self.assertEqual(post_resp.status_code, 200)

        prox_resp = self.client.get("/api/bus/proximity-alerts?lat=13.0827&lng=80.2707&buffer_m=100")
        self.assertEqual(prox_resp.status_code, 200)
        data = prox_resp.json()
        self.assertIn("bus_location", data)
        self.assertIn("alerts_count", data)

    def test_14_aes_crypto_and_encrypted_alert_endpoint(self):
        """Test AES diagnostic endpoint and encrypted alert packet ingestion."""
        # 1. Diagnostic endpoint
        test_payload = {"ping": "pong", "device": "NVIDIA_JETSON_TX2"}
        diag_resp = self.client.post("/api/bus/test-aes-crypto", json=test_payload)
        self.assertEqual(diag_resp.status_code, 200)
        diag_data = diag_resp.json()
        self.assertEqual(diag_data["crypto_health"], "AES-256-GCM OK")
        self.assertEqual(diag_data["decrypted_verification"], test_payload)

        # 2. Encrypt an incident packet using client crypto_engine
        incident_data = {
            "category": "POLICE",
            "hazard_type": "accident_collision",
            "title": "Encrypted Telemetry Test Accident",
            "description": "Transmitted securely over encrypted channel",
            "severity": "CRITICAL",
            "lat": 13.0833,
            "lng": 80.2711,
            "address": "Central Expressway KM 14",
            "geofence_radius": 180.0,
            "speed_kmh": 38.0,
            "confidence": 0.94
        }
        encrypted_packet = crypto_engine.encrypt_gcm(incident_data)

        # Send encrypted packet to API
        post_resp = self.client.post("/api/bus/send-alert-encrypted", json=encrypted_packet)
        self.assertEqual(post_resp.status_code, 200)
        res = post_resp.json()
        self.assertTrue(res["success"])
        self.assertEqual(res["decryption_status"], "AES-256-GCM Verified & Authenticated")
        self.assertEqual(res["assigned_authority"], "POLICE")

    def test_15_ai_vision_inference_simulator(self):
        """Test the /api/predict inference endpoint."""
        resp = self.client.post("/api/predict", data={"simulate_hazard_type": "accident_collision"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["detections_count"], 0)
        self.assertIn("annotated_image", data)
        self.assertTrue(data["annotated_image"].startswith("data:image/jpeg;base64,"))

    def test_16_cloud_sync_and_export_endpoints(self):
        """Test cloud sync status and JSON database export."""
        sync_resp = self.client.get("/api/cloud/sync-status")
        self.assertEqual(sync_resp.status_code, 200)
        sync_data = sync_resp.json()
        self.assertIn("cloud_storage_status", sync_data)
        self.assertIn("supabase", sync_data)

        export_resp = self.client.get("/api/cloud/export-db")
        self.assertEqual(export_resp.status_code, 200)
        exp_data = export_resp.json()
        self.assertIn("incidents", exp_data)
        self.assertIn("crypto_signature", exp_data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
