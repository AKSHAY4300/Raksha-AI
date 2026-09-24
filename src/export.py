import os
import sys
import argparse
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = WORKSPACE_DIR / "models" / "road_vision_best.pt"

def export_model(
    model_path: Path = DEFAULT_MODEL,
    export_format: str = "onnx",
    imgsz: int = 640,
    half: bool = False,
    dynamic: bool = False
):
    print("=" * 65)
    print("ROAD VISION AI - MODEL EXPORTER")
    print("=" * 65)
    print(f"Input Model:  {model_path}")
    print(f"Format:       {export_format}")
    print(f"Image Size:   {imgsz}")
    print("=" * 65)

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    exported_path = model.export(
        format=export_format,
        imgsz=imgsz,
        half=half,
        dynamic=dynamic
    )

    print("\n" + "=" * 65)
    print("EXPORT SUCCESSFUL!")
    print(f"Exported artifact: {exported_path}")
    print("=" * 65)
    return exported_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Road Vision Model")
    parser.add_argument("--model", type=str, default=str(DEFAULT_MODEL), help="Path to .pt model")
    parser.add_argument("--format", type=str, default="onnx", help="Export format (onnx, torchscript, engine)")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution")
    parser.add_argument("--half", action="store_true", help="FP16 half-precision")
    
    args = parser.parse_args()
    export_model(
        model_path=Path(args.model),
        export_format=args.format,
        imgsz=args.imgsz,
        half=args.half
    )
