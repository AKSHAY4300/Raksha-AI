"""
Raksha AI - Central Cloud API Server & Unified Authority Gateway
Dedicated Portals:
1. Traffic Police Headquarters & Highway Accident Control
2. PWD (Public Works Department) Road & Pavement Administration
3. Bus Driver MADT (Mobile/Mounted Alert Display Terminal) Cockpit
4. Bus Edge AI Perception Simulator & AES-256 Cryptographic Hub
5. Cloud Storage (Supabase Free Tier) & Deployment Center
"""

import os
import io
import sys
import json
import base64
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from app.crypto_utils import crypto_engine, DEFAULT_AES_KEY_HEX
from app.database import db, haversine_distance
from app.supabase_client import supabase_adapter

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
DATASETS_DIR = WORKSPACE_DIR / "datasets" / "unified"
MODELS_DIR = WORKSPACE_DIR / "models"
RUNS_DIR = WORKSPACE_DIR / "runs"

app = FastAPI(
    title="Raksha AI - Traffic Police, PWD & Smart Transit Safety Platform",
    description="Edge-to-Cloud AI Perception, AES-256 Telemetry, Geofencing, Police HQ & PWD Dashboards, and Driver MADT HUD",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global YOLO model cache
yolo_model = None
model_load_error = None

def get_model():
    global yolo_model, model_load_error
    if yolo_model is not None:
        return yolo_model

    candidate_paths = [
        MODELS_DIR / "road_vision_best.pt",
        RUNS_DIR / "road_vision" / "unified_detector" / "weights" / "best.pt",
        WORKSPACE_DIR / "yolov8n.pt"
    ]

    for path in candidate_paths:
        if path.exists():
            try:
                from ultralytics import YOLO
                yolo_model = YOLO(str(path))
                model_load_error = None
                return yolo_model
            except Exception as e:
                model_load_error = str(e)

    try:
        from ultralytics import YOLO
        yolo_model = YOLO("yolov8n.pt")
        return yolo_model
    except Exception as e:
        model_load_error = str(e)
        return None

# ==========================================
# 1. SYSTEM STATUS & KPI SUMMARY ENDPOINTS
# ==========================================

@app.get("/api/status")
def get_system_status():
    gpu_available = False
    gpu_name = "CPU (Standard Node)"
    vram_gb = 0.0
    model_loaded = yolo_model is not None
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
    except Exception:
        pass

    kpi = db.get_kpi_stats()
    cloud_status = supabase_adapter.test_connection()

    return {
        "status": "online",
        "system_name": "Raksha AI Police, PWD & Smart Transit Cloud Hub",
        "version": "2.1.0",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
        "encryption": {
            "algorithm": "AES-256-GCM (Authenticated Encryption)",
            "key_fingerprint": crypto_engine.key_hex[:16] + "...",
            "active": True
        },
        "cloud_storage": cloud_status,
        "model_loaded": model_loaded,
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "vram_gb": vram_gb,
        "kpi": kpi
    }

@app.get("/api/kpi-summary")
def get_kpi_summary():
    return db.get_kpi_stats()

# ==========================================
# 2. POLICE HEADQUARTERS ADMIN ENDPOINTS
# ==========================================

@app.get("/api/police-hq/incidents")
def get_police_incidents(status: Optional[str] = None):
    """Fetches all Traffic Police incidents (Accidents, Congestion Gridlocks, Signal Failures, Illegal Parking)."""
    return {
        "authority": "POLICE_HEADQUARTERS",
        "jurisdiction": "State Traffic Police & Highway Accident Quick-Response Command",
        "incidents": db.get_incidents(category="POLICE", status=status)
    }

@app.patch("/api/police-hq/incidents/{incident_id}/acknowledge")
def acknowledge_police_incident(incident_id: str, data: Dict[str, Any] = Body(default={})):
    actor = data.get("actor_name", "Traffic Police Control Room Dispatcher")
    notes = data.get("notes", "Patrol van & traffic wardens dispatched to accident site.")
    updated = db.update_incident_status(incident_id, "ACKNOWLEDGED", actor_name=actor, notes=notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found")
    supabase_adapter.sync_incident_to_cloud(updated)
    return {"success": True, "message": "Incident acknowledged. Traffic patrol en route.", "incident": updated}

@app.patch("/api/police-hq/incidents/{incident_id}/repair")
@app.patch("/api/police-hq/incidents/{incident_id}/clear")
def clear_police_incident(incident_id: str, data: Dict[str, Any] = Body(default={})):
    """Marks traffic incident as Cleared / Resolved. Automatically clears geofence so buses proceed normally."""
    actor = data.get("actor_name", "Highway Patrol Unit #7")
    notes = data.get("notes", "Accident vehicles towed. Debris cleared. All lanes reopened for traffic.")
    updated = db.update_incident_status(incident_id, "REPAIRED", actor_name=actor, notes=notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found")
    supabase_adapter.sync_incident_to_cloud(updated)
    return {
        "success": True,
        "message": "Traffic incident CLEARED! Active geofence removed from transit radar.",
        "incident": updated
    }

# ==========================================
# 3. PWD (PUBLIC WORKS DEPT) ADMIN ENDPOINTS
# ==========================================

@app.get("/api/pwd/incidents")
def get_pwd_incidents(status: Optional[str] = None):
    """Fetches all Civil & Road Infrastructure defects (Potholes, Road Cracks, Open Manholes, Faded Zebra Crossings)."""
    return {
        "authority": "PUBLIC_WORKS_DEPARTMENT",
        "jurisdiction": "State Highways & Municipal Road Maintenance Authority",
        "incidents": db.get_incidents(category="PWD", status=status)
    }

@app.patch("/api/pwd/incidents/{incident_id}/acknowledge")
def acknowledge_pwd_incident(incident_id: str, data: Dict[str, Any] = Body(default={})):
    actor = data.get("actor_name", "PWD Road Maintenance Engineer")
    notes = data.get("notes", "Defect inspected; work order assigned to asphalt contractor.")
    updated = db.update_incident_status(incident_id, "ACKNOWLEDGED", actor_name=actor, notes=notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found")
    supabase_adapter.sync_incident_to_cloud(updated)
    return {"success": True, "message": "Road defect marked as Read / Work Order Scheduled", "incident": updated}

@app.patch("/api/pwd/incidents/{incident_id}/repair")
def repair_pwd_incident(incident_id: str, data: Dict[str, Any] = Body(default={})):
    """Marks road defect as Repaired. Automatically removes geofence so buses are cleared."""
    actor = data.get("actor_name", "PWD Asphalt Patching Crew #4")
    notes = data.get("notes", "Bitumen cold-mix compacted and leveled. Road surface smooth.")
    updated = db.update_incident_status(incident_id, "REPAIRED", actor_name=actor, notes=notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found")
    supabase_adapter.sync_incident_to_cloud(updated)
    return {
        "success": True,
        "message": "Road defect REPAIRED! Geofence removed from transit radar.",
        "incident": updated
    }

# ==========================================
# 4. UNIFIED GEOFENCING & INCIDENT API
# ==========================================

@app.get("/api/geofences/active")
def get_active_geofences():
    """Returns only ACTIVE and ACKNOWLEDGED geofenced danger zones. Excludes REPAIRED/CLEARED areas."""
    geofences = db.get_active_geofences()
    return {
        "total_active": len(geofences),
        "geofences": geofences
    }

@app.patch("/api/incidents/{incident_id}/status")
def update_incident_status_generic(incident_id: str, payload: Dict[str, Any] = Body(...)):
    new_status = payload.get("status", "ACTIVE")
    actor = payload.get("actor_name", "Authority Admin")
    notes = payload.get("notes", "")
    updated = db.update_incident_status(incident_id, new_status, actor_name=actor, notes=notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found")
    supabase_adapter.sync_incident_to_cloud(updated)
    return {"success": True, "incident": updated}

@app.post("/api/incidents/create")
def create_incident_direct(payload: Dict[str, Any] = Body(...)):
    incident = db.create_incident(payload)
    supabase_adapter.sync_incident_to_cloud(incident)
    return {"success": True, "incident": incident}

# ==========================================
# 5. BUS TELEMETRY & DRIVER MADT RADAR API
# ==========================================

@app.get("/api/bus/telemetry")
def get_bus_telemetry():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bus_telemetry")
        rows = cursor.fetchall()
        return {"buses": [dict(r) for r in rows]}

@app.post("/api/bus/telemetry")
def update_bus_telemetry(payload: Dict[str, Any] = Body(...)):
    updated = db.update_bus_telemetry(payload)
    return {"success": True, "telemetry": updated}

@app.get("/api/bus/proximity-alerts")
def check_bus_proximity(
    lat: float = Query(..., description="Current Latitude of the Bus"),
    lng: float = Query(..., description="Current Longitude of the Bus"),
    buffer_m: float = Query(60.0, description="Warning distance buffer in meters")
):
    """
    Computes real-time proximity between moving bus GPS and all active geofences.
    Used by the Driver MADT In-Cabin display to trigger audio-visual warnings.
    """
    alerts = db.check_proximity_alerts(lat, lng, warning_buffer=buffer_m)
    return {
        "bus_location": {"lat": lat, "lng": lng},
        "alerts_count": len(alerts),
        "active_hazard_in_range": len(alerts) > 0,
        "highest_priority_alert": alerts[0] if len(alerts) > 0 else None,
        "all_alerts": alerts
    }

# ==========================================
# 6. AES-256 ENCRYPTED CLOUD TRANSMISSION
# ==========================================

@app.post("/api/bus/send-alert-encrypted")
def receive_encrypted_bus_alert(payload: Dict[str, Any] = Body(...)):
    """
    Receives an AES-256-GCM encrypted alert packet from the Bus Edge AI device.
    Decrypts the payload, validates integrity tag, registers the incident, and creates the geofence.
    """
    try:
        if "ciphertext" not in payload or "iv" not in payload:
            raise HTTPException(status_code=400, detail="Malformed encrypted packet. Missing ciphertext or IV.")

        # Decrypt payload using AES-256-GCM
        decrypted_data = crypto_engine.decrypt_gcm(payload)

        # Register incident in Database
        incident = db.create_incident(decrypted_data)
        supabase_adapter.sync_incident_to_cloud(incident)

        return {
            "success": True,
            "decryption_status": "AES-256-GCM Verified & Authenticated",
            "incident_id": incident["id"],
            "assigned_authority": incident["category"],
            "geofence_created": {
                "lat": incident["lat"],
                "lng": incident["lng"],
                "radius_meters": incident["geofence_radius"]
            },
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AES Decryption / Verification failed: {str(e)}")

@app.post("/api/bus/test-aes-crypto")
def test_aes_crypto_engine(data: Dict[str, Any] = Body(...)):
    """
    Diagnostic endpoint:
    Encrypts provided JSON using AES-256-GCM, returns ciphertext/IV/tag, and verifies round-trip decryption.
    """
    encrypted_packet = crypto_engine.encrypt_gcm(data)
    decrypted_verification = crypto_engine.decrypt_gcm(encrypted_packet)

    return {
        "original_payload": data,
        "encrypted_packet": encrypted_packet,
        "decrypted_verification": decrypted_verification,
        "crypto_health": "AES-256-GCM OK"
    }

# ==========================================
# 7. EDGE AI VISION INFERENCE SIMULATOR
# ==========================================

@app.post("/api/predict")
async def predict_image(
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    sample_filename: Optional[str] = Form(None),
    conf_thresh: float = Form(0.35),
    iou_thresh: float = Form(0.45),
    simulate_hazard_type: Optional[str] = Form(None)
):
    start_time = time.time()
    pil_image = None

    if sample_filename:
        safe_name = Path(sample_filename).name
        sample_path = DATASETS_DIR / "test" / "images" / safe_name
        if not sample_path.exists():
            sample_path = STATIC_DIR / "samples" / safe_name
        if sample_path.exists():
            pil_image = Image.open(sample_path).convert("RGB")

    if pil_image is None and file is not None:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")

    if pil_image is None and image_base64 is not None:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        img_bytes = base64.b64decode(image_base64)
        pil_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    if pil_image is None:
        pil_image = Image.new("RGB", (640, 480), color="#0f172a")

    orig_w, orig_h = pil_image.size
    total_area = orig_w * orig_h
    detections = []
    annotated_img = pil_image.copy()
    draw = ImageDraw.Draw(annotated_img)

    try:
        font = ImageFont.truetype("arial.ttf", size=max(14, int(orig_h * 0.025)))
    except Exception:
        font = ImageFont.load_default()

    # Try YOLO inference
    model = get_model()
    if model is not None and simulate_hazard_type is None:
        try:
            import torch
            device = "0" if torch.cuda.is_available() else "cpu"
            results = model.predict(source=pil_image, conf=conf_thresh, iou=iou_thresh, device=device, verbose=False)
            r = results[0]
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                cls_name = model.names.get(cls_id, f"class_{cls_id}").lower()
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()
                x1, y1, x2, y2 = xyxy
                box_w = x2 - x1
                box_h = y2 - y1
                area_ratio = (box_w * box_h) / total_area if total_area > 0 else 0

                category = "PWD" if any(k in cls_name for k in ["pothole", "zebra"]) else "POLICE"
                label_display = "POTHOLE" if "pothole" in cls_name else ("ZEBRA CROSSING" if "zebra" in cls_name else cls_name.upper())

                det_data = {
                    "class_id": cls_id,
                    "class_name": label_display,
                    "category": category,
                    "confidence": round(conf, 4),
                    "box": {"x1": round(x1, 1), "y1": round(y1, 1), "x2": round(x2, 1), "y2": round(y2, 1)},
                    "area_ratio": round(area_ratio, 4),
                    "severity": "CRITICAL" if area_ratio > 0.06 else ("HIGH" if area_ratio > 0.02 else "MODERATE"),
                    "color": "#ff3b5c" if category == "PWD" else "#ef4444"
                }
                detections.append(det_data)
                draw.rectangle([x1, y1, x2, y2], outline=(255, 59, 92), width=3)
                draw.text((x1 + 6, max(0, y1 - 22)), f"{label_display} ({int(conf*100)}%)", fill=(255, 255, 255), font=font)
        except Exception as e:
            print("YOLO inference fallback:", e)

    # Simulation fallback
    if len(detections) == 0:
        sim_type = simulate_hazard_type or "accident_collision"
        if sim_type in ["accident_collision", "traffic_congestion"]:
            detections.append({
                "class_id": 10,
                "class_name": "VEHICLE COLLISION ACCIDENT",
                "category": "POLICE",
                "confidence": 0.95,
                "box": {"x1": 80, "y1": 90, "x2": 560, "y2": 320},
                "area_ratio": 0.22,
                "severity": "CRITICAL",
                "color": "#ef4444"
            })
            draw.rectangle([80, 90, 560, 320], outline=(239, 68, 68), width=4)
            draw.text((90, 98), "POLICE INCIDENT: MULTI-VEHICLE CRASH (LANES 1 & 2 BLOCKED)", fill=(255, 255, 255), font=font)
        elif sim_type == "pothole":
            detections.append({
                "class_id": 0,
                "class_name": "ROAD POTHOLE",
                "category": "PWD",
                "confidence": 0.96,
                "box": {"x1": 180, "y1": 220, "x2": 460, "y2": 380},
                "area_ratio": 0.14,
                "severity": "CRITICAL",
                "color": "#ff3b5c"
            })
            draw.rectangle([180, 220, 460, 380], outline=(255, 59, 92), width=4)
            draw.text((190, 228), "PWD HAZARD: DEEP ASPHALT CAVITY (1.4m)", fill=(255, 255, 255), font=font)

    buffered = io.BytesIO()
    annotated_img.save(buffered, format="JPEG", quality=90)
    annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")

    total_time_ms = (time.time() - start_time) * 1000.0

    return {
        "success": True,
        "detections_count": len(detections),
        "detections": detections,
        "timing": {
            "total_ms": round(total_time_ms, 2),
            "fps": round(1000.0 / total_time_ms, 1) if total_time_ms > 0 else 0
        },
        "annotated_image": annotated_b64
    }

# ==========================================
# 8. CLOUD STORAGE & BACKUP API
# ==========================================

@app.get("/api/cloud/sync-status")
def get_cloud_sync_status():
    all_incidents = db.get_incidents()
    supabase_test = supabase_adapter.test_connection()
    return {
        "cloud_storage_status": "Supabase Free Cloud Storage Adapter Active",
        "persistent_engine": "SQLite3 + Supabase PostgreSQL Cloud Sync",
        "supabase": supabase_test,
        "local_record_count": len(all_incidents),
        "active_geofences_count": len([i for i in all_incidents if i["status"] not in ["REPAIRED", "CLEARED"]]),
        "aes_key_configured": len(DEFAULT_AES_KEY_HEX) == 64
    }

@app.get("/api/cloud/export-db")
def export_database_json():
    incidents = db.get_incidents()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bus_telemetry")
        telemetry = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50")
        audit_logs = [dict(r) for r in cursor.fetchall()]

    return {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
        "incidents": incidents,
        "telemetry": telemetry,
        "audit_logs": audit_logs,
        "crypto_signature": hashlib.sha256(json.dumps(incidents, default=str).encode('utf-8')).hexdigest()
    }

# Mount static files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
@app.get("/police-hq", response_class=HTMLResponse)
@app.get("/pwd-admin", response_class=HTMLResponse)
@app.get("/driver-madt", response_class=HTMLResponse)
@app.get("/bus-edge", response_class=HTMLResponse)
@app.get("/cloud-deploy", response_class=HTMLResponse)
def serve_portal(request: Request):
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Raksha AI Server Running. (index.html not found)</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="127.0.0.1", port=8000, reload=False)
