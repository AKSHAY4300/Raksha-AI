import os
import sys
import json
import argparse
import time
from pathlib import Path
import torch

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
DATA_YAML = WORKSPACE_DIR / "datasets" / "unified" / "data.yaml"
DEFAULT_MODEL = WORKSPACE_DIR / "models" / "road_vision_best.pt"

def evaluate_model(
    model_path: Path = DEFAULT_MODEL,
    data_yaml: Path = DATA_YAML,
    split: str = "test",
    imgsz: int = 640,
    batch_size: int = 16,
    device: str = "0" if torch.cuda.is_available() else "cpu"
):
    print("=" * 65)
    print("ROAD VISION AI - MODEL EVALUATION & BENCHMARK")
    print("=" * 65)
    print(f"Model Path:  {model_path}")
    print(f"Dataset:     {data_yaml} ({split} split)")
    print(f"Device:      {device}")
    print("=" * 65)

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model weights not found at {model_path}. Train the model first!")

    from ultralytics import YOLO

    model = YOLO(str(model_path))

    # Run validation on the specified split
    metrics = model.val(
        data=str(data_yaml),
        split=split,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        project=str(WORKSPACE_DIR / "runs" / "eval"),
        name=f"eval_{split}",
        plots=True,
        verbose=True
    )

    # Extract metrics
    results_summary = {
        "split": split,
        "model_path": str(model_path),
        "overall": {
            "mAP50": float(metrics.box.map50),
            "mAP50_95": float(metrics.box.map),
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
            "fitness": float(metrics.fitness)
        },
        "speed": {
            "preprocess_ms": float(metrics.speed.get("preprocess", 0.0)),
            "inference_ms": float(metrics.speed.get("inference", 0.0)),
            "postprocess_ms": float(metrics.speed.get("loss", 0.0) + metrics.speed.get("postprocess", 0.0)),
            "total_latency_ms": float(sum(metrics.speed.values())),
            "fps": float(1000.0 / sum(metrics.speed.values())) if sum(metrics.speed.values()) > 0 else 0.0
        },
        "per_class": {}
    }

    # Per-class breakdown
    class_names = ["pothole", "zebra_crossing"]
    for i, cname in enumerate(class_names):
        if i < len(metrics.box.maps):
            results_summary["per_class"][cname] = {
                "class_id": i,
                "mAP50": float(metrics.box.maps[i]),
                "precision": float(metrics.box.p[i]) if len(metrics.box.p) > i else 0.0,
                "recall": float(metrics.box.r[i]) if len(metrics.box.r) > i else 0.0
            }

    # Save metrics JSON
    out_dir = WORKSPACE_DIR / "runs" / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"metrics_{split}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    print("\n" + "=" * 65)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 65)
    print(f"Overall mAP@0.5:       {results_summary['overall']['mAP50'] * 100:.2f}%")
    print(f"Overall mAP@0.5:0.95:  {results_summary['overall']['mAP50_95'] * 100:.2f}%")
    print(f"Overall Precision:     {results_summary['overall']['precision'] * 100:.2f}%")
    print(f"Overall Recall:        {results_summary['overall']['recall'] * 100:.2f}%")
    print(f"Inference Latency:     {results_summary['speed']['inference_ms']:.2f} ms ({results_summary['speed']['fps']:.1f} FPS)")
    print("-" * 65)
    print("Per-Class Metrics:")
    for cname, cdata in results_summary["per_class"].items():
        print(f"  [{cname.upper()}] mAP50: {cdata['mAP50']*100:.2f}% | Precision: {cdata['precision']*100:.2f}% | Recall: {cdata['recall']*100:.2f}%")
    print("=" * 65)
    print(f"Full metrics saved to: {json_path}")
    return results_summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Road Vision AI Model")
    parser.add_argument("--model", type=str, default=str(DEFAULT_MODEL), help="Path to model weights (.pt)")
    parser.add_argument("--split", type=str, default="test", help="Split to evaluate on (test/valid/train)")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--device", type=str, default="0" if torch.cuda.is_available() else "cpu", help="Device")
    
    args = parser.parse_args()
    evaluate_model(
        model_path=Path(args.model),
        split=args.split,
        batch_size=args.batch,
        device=args.device
    )
