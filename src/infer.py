import os
import sys
import argparse
import time
from pathlib import Path
import json

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = WORKSPACE_DIR / "models" / "road_vision_best.pt"
OUTPUT_DIR = WORKSPACE_DIR / "runs" / "inference"

CLASS_NAMES = {
    0: "pothole",
    1: "zebra_crossing"
}

CLASS_COLORS = {
    "pothole": (0, 0, 255),        # Red (BGR)
    "zebra_crossing": (0, 255, 0)   # Green (BGR)
}

def estimate_pothole_severity(bbox_area_ratio: float) -> str:
    """Classify pothole severity based on normalized bounding box area."""
    if bbox_area_ratio > 0.08:
        return "CRITICAL (High Hazard)"
    elif bbox_area_ratio > 0.03:
        return "MODERATE (Caution Required)"
    else:
        return "MINOR (Surface Defect)"

def run_inference(
    source: str,
    model_path: Path = DEFAULT_MODEL,
    conf_thresh: float = 0.35,
    iou_thresh: float = 0.45,
    device: str = "0",
    save_output: bool = True,
    output_dir: Path = OUTPUT_DIR
):
    print("=" * 65)
    print("ROAD VISION AI - INFERENCE ENGINE")
    print("=" * 65)
    print(f"Source:      {source}")
    print(f"Model:       {model_path}")
    print(f"Confidence:  {conf_thresh}")
    print(f"Device:      {device}")
    print("=" * 65)

    from ultralytics import YOLO
    import cv2
    import numpy as np

    if not Path(model_path).exists():
        # Fallback to YOLO base model if custom not trained yet
        print(f"Notice: Custom model {model_path} not found, checking fallback...")
        fallback = WORKSPACE_DIR / "runs" / "road_vision" / "unified_detector" / "weights" / "best.pt"
        if fallback.exists():
            model_path = fallback
        else:
            print("Please ensure model is trained or specify valid weights.")

    model = YOLO(str(model_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    results = model.predict(
        source=source,
        conf=conf_thresh,
        iou=iou_thresh,
        device=device,
        save=save_output,
        project=str(output_dir),
        name="predict",
        exist_ok=True
    )

    all_detections = []

    for idx, r in enumerate(results):
        img_name = Path(r.path).name if hasattr(r, "path") and r.path else f"frame_{idx}.jpg"
        img_detections = {
            "image": img_name,
            "orig_shape": r.orig_shape,
            "detections": []
        }
        
        orig_h, orig_w = r.orig_shape[:2]
        total_img_area = orig_h * orig_w

        for box in r.boxes:
            cls_id = int(box.cls[0].item())
            cls_name = model.names.get(cls_id, f"class_{cls_id}")
            conf = float(box.conf[0].item())
            xyxy = box.xyxy[0].tolist()
            xywhn = box.xywhn[0].tolist()
            
            bbox_w = xyxy[2] - xyxy[0]
            bbox_h = xyxy[3] - xyxy[1]
            bbox_area = bbox_w * bbox_h
            area_ratio = bbox_area / total_img_area if total_img_area > 0 else 0

            det_info = {
                "class_id": cls_id,
                "class_name": cls_name,
                "confidence": round(conf, 4),
                "box_xyxy": [round(x, 1) for x in xyxy],
                "box_xywh_norm": [round(x, 4) for x in xywhn],
                "area_ratio": round(area_ratio, 4)
            }

            if cls_name == "pothole" or cls_id == 0:
                det_info["severity"] = estimate_pothole_severity(area_ratio)
            elif cls_name == "zebra_crossing" or cls_id == 1:
                det_info["type"] = "Pedestrian Safety Zone"

            img_detections["detections"].append(det_info)

        all_detections.append(img_detections)
        print(f"[{img_name}] Detected {len(img_detections['detections'])} objects: {[d['class_name'] for d in img_detections['detections']]}")

    # Save detections JSON
    json_out = output_dir / "predict" / "detections.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(all_detections, f, indent=2)

    print(f"\nInference complete. Detections saved to {json_out}")
    return all_detections

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Road Vision AI Inference CLI")
    parser.add_argument("--source", type=str, required=True, help="Path to image, folder, video, or webcam index (0)")
    parser.add_argument("--model", type=str, default=str(DEFAULT_MODEL), help="Path to model weights (.pt)")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold (0.0 - 1.0)")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold")
    parser.add_argument("--device", type=str, default="0", help="Device (0 for GPU, cpu)")
    
    args = parser.parse_args()
    run_inference(
        source=args.source,
        model_path=Path(args.model),
        conf_thresh=args.conf,
        iou_thresh=args.iou,
        device=args.device
    )
