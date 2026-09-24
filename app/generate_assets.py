"""
Generates visual reference sample images for Police HQ and PWD hazards.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

STATIC_DIR = Path(__file__).resolve().parent / "static"
SAMPLES_DIR = STATIC_DIR / "samples"

def create_sample_assets():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    
    samples = [
        # Police Traffic & Accident Samples
        ("police_accident_collision.jpg", "TRAFFIC POLICE: VEHICLE COLLISION", "#0a0f1d", "#ef4444", "Multi-Vehicle Crash (Lanes 1 & 2 Blocked)"),
        ("police_traffic_jam.jpg", "TRAFFIC POLICE: HEAVY GRIDLOCK", "#0a0f1d", "#f59e0b", "Truck Breakdown / 1.5km Backup"),
        ("police_signal_failure.jpg", "TRAFFIC POLICE: SIGNAL MALFUNCTION", "#0a0f1d", "#ef4444", "Intersection Signal Outage / High Collision Risk"),
        ("police_illegal_parking.jpg", "TRAFFIC POLICE: ILLEGAL BUS BAY PARKING", "#0a0f1d", "#3b82f6", "Commercial Vehicle Blocking Public Transit Stop"),
        # PWD Civil Road Samples
        ("pothole_severe.jpg", "PWD ROAD DEFECT: CRITICAL POTHOLE", "#0a0f1d", "#ef4444", "Depth 18cm / Width 1.4m Crater"),
        ("pothole_cluster.jpg", "PWD ROAD DEFECT: POTHOLE CLUSTER", "#0a0f1d", "#f59e0b", "Surface Fracture Zone (12m Span)"),
        ("faded_zebra.jpg", "PWD ROAD DEFECT: FADED ZEBRA CROSSING", "#0a0f1d", "#10b981", "Pedestrian Marking 85% Degraded"),
        ("open_manhole.jpg", "PWD ROAD DEFECT: OPEN MANHOLE", "#0a0f1d", "#ef4444", "Stormwater Drain Trap (Fatal Vehicle Hazard)")
    ]

    for filename, title, bg_color, accent_color, subtitle in samples:
        img = Image.new("RGB", (640, 400), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw grid background
        for x in range(0, 640, 40):
            draw.line([(x, 0), (x, 400)], fill="#1e293b", width=1)
        for y in range(0, 400, 40):
            draw.line([(0, y), (640, y)], fill="#1e293b", width=1)

        # Draw border frame
        draw.rectangle([10, 10, 630, 390], outline=accent_color, width=3)
        
        # Bounding box mockup
        draw.rectangle([100, 80, 540, 310], outline=accent_color, width=4)
        draw.rectangle([100, 80, 340, 115], fill=accent_color)
        
        # Text
        try:
            font = ImageFont.truetype("arial.ttf", 20)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font = ImageFont.load_default()
            small_font = font

        draw.text((110, 88), "AI DETECTED INCIDENT", fill="#ffffff", font=font)
        draw.text((30, 30), title, fill=accent_color, font=font)
        draw.text((30, 350), subtitle, fill="#94a3b8", font=small_font)
        draw.text((430, 350), "EDGE BUS GPS LOCK", fill="#10b981", font=small_font)

        img.save(SAMPLES_DIR / filename, "JPEG", quality=90)
        print(f"Generated sample: {filename}")

if __name__ == "__main__":
    create_sample_assets()
