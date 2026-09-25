"""
Raksha AI - Persistent Data Management & Geofencing Engine
Supports SQLite / JSON persistence, spatial proximity query, and Supabase Cloud sync.
Categories:
- 'POLICE': Traffic Police Headquarters & Highway Accident Control (Accidents, Traffic Jams, Signal Failures, Illegal Parking)
- 'PWD': Public Works Department (Potholes, Road Cracks, Faded Zebra Crossings, Open Manholes)
"""

import os
import sqlite3
import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

def _get_data_dir() -> Path:
    # Always use /tmp on Vercel, AWS Lambda, or any environment where local dir is read-only
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"):
        return Path("/tmp") / "data"

    local_dir = Path(__file__).resolve().parent / "data"
    try:
        local_dir.mkdir(parents=True, exist_ok=True)
        test_file = local_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        return local_dir
    except Exception:
        return Path("/tmp") / "data"

DATA_DIR = _get_data_dir()
DB_PATH = DATA_DIR / "vision_ai.db"

# Haversine spherical distance in meters between two GPS lat/lng points
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class DatabaseManager:
    def __init__(self):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self.init_db()
        self.seed_initial_data_if_empty()

    def get_connection(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Incidents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,         -- 'POLICE' or 'PWD'
                    hazard_type TEXT NOT NULL,      -- 'accident_collision', 'traffic_congestion', 'pothole', etc.
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL,         -- 'CRITICAL', 'HIGH', 'MODERATE', 'MINOR'
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    address TEXT,
                    geofence_radius REAL DEFAULT 150.0, -- In meters
                    status TEXT NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'ACKNOWLEDGED', 'CLEARED' / 'REPAIRED'
                    bus_id TEXT DEFAULT 'BUS-104',
                    speed_kmh REAL DEFAULT 42.0,
                    confidence REAL DEFAULT 0.92,
                    image_url TEXT,
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    acknowledged_by TEXT,
                    repaired_at TEXT,
                    repaired_by TEXT,
                    repair_notes TEXT,
                    encrypted_packet_hash TEXT
                )
            """)

            # Bus Telemetry table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bus_telemetry (
                    bus_id TEXT PRIMARY KEY,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    speed_kmh REAL NOT NULL,
                    heading REAL NOT NULL,
                    route_id TEXT NOT NULL,
                    route_name TEXT NOT NULL,
                    driver_name TEXT DEFAULT 'M. Sundaram',
                    last_ping TEXT NOT NULL
                )
            """)

            # Audit / Action logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    incident_id TEXT,
                    bus_id TEXT,
                    details TEXT
                )
            """)
            conn.commit()

    def seed_initial_data_if_empty(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Reset table if it has legacy 'POWER' records
            cursor.execute("SELECT COUNT(*) FROM incidents WHERE category = 'POWER'")
            legacy_count = cursor.fetchone()[0]
            if legacy_count > 0:
                cursor.execute("DELETE FROM incidents")
                conn.commit()

            cursor.execute("SELECT COUNT(*) FROM incidents")
            count = cursor.fetchone()[0]
            if count > 0:
                return

            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

            # Seed realistic Traffic Police & PWD incidents
            sample_incidents = [
                # --- POLICE HEADQUARTERS HAZARDS (Traffic & Accident Control) ---
                {
                    "id": "INC-POL-2026-001",
                    "category": "POLICE",
                    "hazard_type": "accident_collision",
                    "title": "Major Vehicle Collision Blocking Bus Lane",
                    "description": "Two passenger cars and a mini-truck collided at intersection. Lane 1 and Lane 2 completely blocked. Debris across road. Immediate traffic patrol and ambulance required.",
                    "severity": "CRITICAL",
                    "lat": 13.0838,
                    "lng": 80.2745,
                    "address": "EVR Periyar Salai, near Central Railway Gate",
                    "geofence_radius": 180.0,
                    "status": "ACTIVE",
                    "bus_id": "BUS-104",
                    "speed_kmh": 38.5,
                    "confidence": 0.95,
                    "image_url": "/static/samples/police_accident_collision.jpg",
                    "created_at": now
                },
                {
                    "id": "INC-POL-2026-002",
                    "category": "POLICE",
                    "hazard_type": "traffic_congestion",
                    "title": "Heavy Vehicle Breakdown & Gridlock Bottleneck",
                    "description": "Overloaded commercial truck broken down on central transit corridor causing 1.5km vehicular backup. Traffic police diversion required.",
                    "severity": "HIGH",
                    "lat": 13.0760,
                    "lng": 80.2610,
                    "address": "Poonamallee High Rd, Kilpauk Junction",
                    "geofence_radius": 160.0,
                    "status": "ACTIVE",
                    "bus_id": "BUS-102",
                    "speed_kmh": 41.0,
                    "confidence": 0.91,
                    "image_url": "/static/samples/police_traffic_jam.jpg",
                    "created_at": now
                },
                {
                    "id": "INC-POL-2026-003",
                    "category": "POLICE",
                    "hazard_type": "signal_failure",
                    "title": "Traffic Signal Malfunction at Busy Intersection",
                    "description": "Automated 4-way traffic signals offline due to power surge. Severe risk of cross-traffic collisions. Traffic wardens urgently assigned.",
                    "severity": "CRITICAL",
                    "lat": 13.0645,
                    "lng": 80.2480,
                    "address": "Anna Salai, Gemini Flyover Underpass",
                    "geofence_radius": 200.0,
                    "status": "ACKNOWLEDGED",
                    "bus_id": "BUS-107",
                    "speed_kmh": 28.0,
                    "confidence": 0.89,
                    "image_url": "/static/samples/police_signal_failure.jpg",
                    "created_at": now,
                    "acknowledged_at": now,
                    "acknowledged_by": "Traffic Police Control Room - Sector 2"
                },
                {
                    "id": "INC-POL-2026-004",
                    "category": "POLICE",
                    "hazard_type": "illegal_parking",
                    "title": "Illegal Roadside Heavy Vehicle Parking in Bus Bay",
                    "description": "Commercial cargo vehicles parked illegally in dedicated public bus stop bay, forcing buses into oncoming traffic lane.",
                    "severity": "MODERATE",
                    "lat": 13.0512,
                    "lng": 80.2520,
                    "address": "Cathedral Road, Near Semmozhi Poonga",
                    "geofence_radius": 130.0,
                    "status": "ACTIVE",
                    "bus_id": "BUS-101",
                    "speed_kmh": 45.0,
                    "confidence": 0.88,
                    "image_url": "/static/samples/police_illegal_parking.jpg",
                    "created_at": now
                },

                # --- PWD ROAD DEFECT HAZARDS (Civil Highways Infrastructure) ---
                {
                    "id": "INC-PWD-2026-001",
                    "category": "PWD",
                    "hazard_type": "pothole",
                    "title": "Severe Deep Asphalt Pothole Crater (1.4m Width)",
                    "description": "Severe road crater with jagged asphalt edges in central transit lane. High risk of bus axle/tire damage and vehicle swerving.",
                    "severity": "CRITICAL",
                    "lat": 13.0805,
                    "lng": 80.2690,
                    "address": "Gandhi Irwin Bridge Road, Egmore Approach",
                    "geofence_radius": 140.0,
                    "status": "ACTIVE",
                    "bus_id": "BUS-104",
                    "speed_kmh": 34.0,
                    "confidence": 0.96,
                    "image_url": "/static/samples/pothole_severe.jpg",
                    "created_at": now
                },
                {
                    "id": "INC-PWD-2026-002",
                    "category": "PWD",
                    "hazard_type": "pothole",
                    "title": "Cluster of Surface Asphalt Potholes (12m Span)",
                    "description": "Multiple consecutive road cavities along the outer bus lane.",
                    "severity": "HIGH",
                    "lat": 13.0690,
                    "lng": 80.2550,
                    "address": "Pantheon Road, Egmore Museum Signal",
                    "geofence_radius": 130.0,
                    "status": "ACTIVE",
                    "bus_id": "BUS-108",
                    "speed_kmh": 40.0,
                    "confidence": 0.92,
                    "image_url": "/static/samples/pothole_cluster.jpg",
                    "created_at": now
                },
                {
                    "id": "INC-PWD-2026-003",
                    "category": "PWD",
                    "hazard_type": "faded_zebra",
                    "title": "Severely Faded School-Zone Zebra Crossing",
                    "description": "Pedestrian crossing markings degraded by over 80%; invisible at night to oncoming vehicles near Government Higher Secondary School.",
                    "severity": "HIGH",
                    "lat": 13.0580,
                    "lng": 80.2505,
                    "address": "Sterling Road, Nungambakkam High Rd",
                    "geofence_radius": 120.0,
                    "status": "ACKNOWLEDGED",
                    "bus_id": "BUS-104",
                    "speed_kmh": 35.0,
                    "confidence": 0.95,
                    "image_url": "/static/samples/faded_zebra.jpg",
                    "created_at": now,
                    "acknowledged_at": now,
                    "acknowledged_by": "PWD Road Maintenance Division 5"
                },
                {
                    "id": "INC-PWD-2026-004",
                    "category": "PWD",
                    "hazard_type": "open_manhole",
                    "title": "Displaced Heavy Storm-Drain Manhole Cover",
                    "description": "Cast iron stormwater drain lid displaced by 40cm, creating an open wheel-trap on right lane.",
                    "severity": "CRITICAL",
                    "lat": 13.0450,
                    "lng": 80.2410,
                    "address": "Mount Road, Teynampet Metro Gate B",
                    "geofence_radius": 160.0,
                    "status": "ACTIVE",
                    "bus_id": "BUS-110",
                    "speed_kmh": 29.0,
                    "confidence": 0.93,
                    "image_url": "/static/samples/open_manhole.jpg",
                    "created_at": now
                }
            ]

            for inc in sample_incidents:
                cursor.execute("""
                    INSERT INTO incidents (
                        id, category, hazard_type, title, description, severity,
                        lat, lng, address, geofence_radius, status, bus_id,
                        speed_kmh, confidence, image_url, created_at,
                        acknowledged_at, acknowledged_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inc["id"], inc["category"], inc["hazard_type"], inc["title"],
                    inc["description"], inc["severity"], inc["lat"], inc["lng"],
                    inc["address"], inc["geofence_radius"], inc["status"],
                    inc["bus_id"], inc["speed_kmh"], inc["confidence"],
                    inc["image_url"], inc["created_at"],
                    inc.get("acknowledged_at"), inc.get("acknowledged_by")
                ))

            # Initial Bus Fleet Telemetry
            cursor.execute("""
                INSERT OR REPLACE INTO bus_telemetry (
                    bus_id, lat, lng, speed_kmh, heading, route_id, route_name, driver_name, last_ping
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "BUS-104", 13.0850, 80.2760, 42.5, 215.0, "ROUTE-19B",
                "Route 19B (Central Station ➔ T. Nagar Express)", "M. Sundaram", now
            ))

            conn.commit()

    def get_incidents(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM incidents WHERE 1=1"
            params = []
            if category:
                query += " AND category = ?"
                params.append(category.upper())
            if status:
                query += " AND status = ?"
                params.append(status.upper())
            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_active_geofences(self) -> List[Dict[str, Any]]:
        """Returns only ACTIVE and ACKNOWLEDGED incidents (excluding CLEARED / REPAIRED)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, category, hazard_type, title, description, severity,
                       lat, lng, address, geofence_radius, status, created_at
                FROM incidents
                WHERE status NOT IN ('REPAIRED', 'CLEARED')
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_incident_status(self, incident_id: str, new_status: str, actor_name: str = "Admin", notes: str = "") -> Optional[Dict[str, Any]]:
        new_status = new_status.upper()
        if new_status in ["REPAIRED", "CLEARED"]:
            canonical_status = "REPAIRED"
        elif new_status == "ACKNOWLEDGED":
            canonical_status = "ACKNOWLEDGED"
        else:
            canonical_status = "ACTIVE"

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            row = cursor.fetchone()
            if not row:
                return None

            if canonical_status == "ACKNOWLEDGED":
                cursor.execute("""
                    UPDATE incidents
                    SET status = 'ACKNOWLEDGED', acknowledged_at = ?, acknowledged_by = ?, repair_notes = ?
                    WHERE id = ?
                """, (now, actor_name, notes, incident_id))
            elif canonical_status == "REPAIRED":
                cursor.execute("""
                    UPDATE incidents
                    SET status = 'REPAIRED', repaired_at = ?, repaired_by = ?, repair_notes = ?
                    WHERE id = ?
                """, (now, actor_name, notes, incident_id))
            elif canonical_status == "ACTIVE":
                cursor.execute("""
                    UPDATE incidents
                    SET status = 'ACTIVE', repaired_at = NULL, repaired_by = NULL
                    WHERE id = ?
                """, (incident_id,))

            # Log audit trail
            cursor.execute("""
                INSERT INTO audit_logs (timestamp, event_type, category, incident_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (now, f"STATUS_CHANGE_{canonical_status}", row["category"], incident_id, f"Changed by {actor_name}. Notes: {notes}"))

            conn.commit()

            cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            return dict(cursor.fetchone())

    def create_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        category = incident_data.get("category", "POLICE").upper()
        inc_id = incident_data.get("id") or f"INC-{category[:3]}-{int(time.time()*1000)}"
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO incidents (
                    id, category, hazard_type, title, description, severity,
                    lat, lng, address, geofence_radius, status, bus_id,
                    speed_kmh, confidence, image_url, created_at, encrypted_packet_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inc_id,
                category,
                incident_data.get("hazard_type", "accident_collision"),
                incident_data.get("title", "Road Incident Detected"),
                incident_data.get("description", "Detected by Bus Edge AI Perception"),
                incident_data.get("severity", "HIGH").upper(),
                float(incident_data.get("lat", 13.0827)),
                float(incident_data.get("lng", 80.2707)),
                incident_data.get("address", "Metropolitan Highway Corridor"),
                float(incident_data.get("geofence_radius", 160.0)),
                "ACTIVE",
                incident_data.get("bus_id", "BUS-104"),
                float(incident_data.get("speed_kmh", 40.0)),
                float(incident_data.get("confidence", 0.92)),
                incident_data.get("image_url", ""),
                now,
                incident_data.get("encrypted_packet_hash", "")
            ))

            cursor.execute("""
                INSERT INTO audit_logs (timestamp, event_type, category, incident_id, bus_id, details)
                VALUES (?, 'INCIDENT_CREATED', ?, ?, ?, ?)
            """, (now, category, inc_id, incident_data.get("bus_id", "BUS-104"), incident_data.get("title", "")))

            conn.commit()
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (inc_id,))
            return dict(cursor.fetchone())

    def update_bus_telemetry(self, bus_data: Dict[str, Any]) -> Dict[str, Any]:
        bus_id = bus_data.get("bus_id", "BUS-104")
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO bus_telemetry (
                    bus_id, lat, lng, speed_kmh, heading, route_id, route_name, driver_name, last_ping
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bus_id,
                float(bus_data.get("lat", 13.0827)),
                float(bus_data.get("lng", 80.2707)),
                float(bus_data.get("speed_kmh", 40.0)),
                float(bus_data.get("heading", 0.0)),
                bus_data.get("route_id", "ROUTE-19B"),
                bus_data.get("route_name", "City Central Express"),
                bus_data.get("driver_name", "Driver A"),
                now
            ))
            conn.commit()
            cursor.execute("SELECT * FROM bus_telemetry WHERE bus_id = ?", (bus_id,))
            return dict(cursor.fetchone())

    def check_proximity_alerts(self, bus_lat: float, bus_lng: float, warning_buffer: float = 60.0) -> List[Dict[str, Any]]:
        """
        Computes distance between the bus and all ACTIVE/ACKNOWLEDGED geofenced hazard zones.
        Returns a list of alerts if the bus is within (geofence_radius + warning_buffer).
        """
        active_hazards = self.get_active_geofences()
        alerts = []

        for hazard in active_hazards:
            dist_meters = haversine_distance(bus_lat, bus_lng, hazard["lat"], hazard["lng"])
            alert_range = hazard["geofence_radius"] + warning_buffer

            if dist_meters <= alert_range:
                alerts.append({
                    "incident_id": hazard["id"],
                    "category": hazard["category"],
                    "hazard_type": hazard["hazard_type"],
                    "title": hazard["title"],
                    "description": hazard["description"],
                    "severity": hazard["severity"],
                    "address": hazard["address"],
                    "lat": hazard["lat"],
                    "lng": hazard["lng"],
                    "geofence_radius": hazard["geofence_radius"],
                    "distance_meters": round(dist_meters, 1),
                    "is_inside": dist_meters <= hazard["geofence_radius"],
                    "recommended_speed_kmh": 15.0 if hazard["severity"] == "CRITICAL" else 25.0,
                    "priority": 1 if hazard["severity"] == "CRITICAL" else (2 if hazard["severity"] == "HIGH" else 3)
                })

        # Sort by distance (closest first)
        alerts.sort(key=lambda x: x["distance_meters"])
        return alerts

    def get_kpi_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, status, severity, COUNT(*) FROM incidents GROUP BY category, status, severity")
            rows = cursor.fetchall()

            stats = {
                "police": {"total": 0, "active": 0, "acknowledged": 0, "repaired": 0, "critical": 0},
                "pwd": {"total": 0, "active": 0, "acknowledged": 0, "repaired": 0, "critical": 0},
                "total_active_geofences": 0
            }

            for row in rows:
                cat = row[0].lower()
                status = row[1].lower()
                sev = row[2].upper()
                cnt = row[3]

                if cat in stats:
                    stats[cat]["total"] += cnt
                    if status == "active":
                        stats[cat]["active"] += cnt
                        stats["total_active_geofences"] += cnt
                    elif status == "acknowledged":
                        stats[cat]["acknowledged"] += cnt
                        stats["total_active_geofences"] += cnt
                    elif status in ["repaired", "cleared"]:
                        stats[cat]["repaired"] += cnt

                    if sev == "CRITICAL" and status not in ["repaired", "cleared"]:
                        stats[cat]["critical"] += cnt

            return stats

# Global Database Singleton
db = DatabaseManager()
