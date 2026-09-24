import os
import sys
import argparse
import shutil
from pathlib import Path
import torch

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
DATA_YAML = WORKSPACE_DIR / "datasets" / "unified" / "data.yaml"
MODELS_DIR = WORKSPACE_DIR / "models"

def train_model(
    model_variant: str = "yolov8n.pt",
    epochs: int = 30,
    batch_size: int = 16,
    imgsz: int = 640,
    device: str = "0" if torch.cuda.is_available() else "cpu",
    project_name: str = "road_vision",
    run_name: str = "unified_detector",
    lr0: float = 0.01,
    patience: int = 10,
    workers: int = 4
):
    print("=" * 65)
    print("ROAD VISION AI - MODEL TRAINING PIPELINE")
    print("=" * 65)
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available:  {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Device:      {torch.cuda.get_device_name(0)}")
        print(f"VRAM:            {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    print(f"Data Config:     {DATA_YAML}")
    print(f"Base Model:      {model_variant}")
    print(f"Epochs:          {epochs}")
    print(f"Batch Size:      {batch_size}")
    print(f"Image Size:      {imgsz}")
    print(f"Device:          {device}")
    print("=" * 65)

    if not DATA_YAML.exists():
        raise FileNotFoundError(f"data.yaml not found at {DATA_YAML}. Run src/dataset_prep.py first!")

    from ultralytics import YOLO

    # Initialize model with pre-trained weights
    model = YOLO(model_variant)

    # Train the model
    results = model.train(
        data=str(DATA_YAML),
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        device=device,
        project=str(WORKSPACE_DIR / "runs" / project_name),
        name=run_name,
        patience=patience,
        lr0=lr0,
        workers=workers,
        optimizer="auto",
        save=True,
        save_period=5,
        val=True,
        plots=True,
        verbose=True,
        exist_ok=True,
        amp=True  # Automatic Mixed Precision for RTX GPU acceleration
    )

    # Copy best weights to models/ folder for deployment
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    best_weights_path = Path(results.save_dir) / "weights" / "best.pt"
    if best_weights_path.exists():
        dest_best = MODELS_DIR / "road_vision_best.pt"
        shutil.copy2(best_weights_path, dest_best)
        print(f"\nSaved best model weights to: {dest_best}")
        
    last_weights_path = Path(results.save_dir) / "weights" / "last.pt"
    if last_weights_path.exists():
        dest_last = MODELS_DIR / "road_vision_last.pt"
        shutil.copy2(last_weights_path, dest_last)

    print("\n" + "=" * 65)
    print("TRAINING COMPLETE!")
    print(f"Results saved in: {results.save_dir}")
    print("=" * 65)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Road Vision Object Detection Model")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Base model (yolov8n.pt, yolo11n.pt, yolov8s.pt)")
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution")
    parser.add_argument("--device", type=str, default="0" if torch.cuda.is_available() else "cpu", help="Device (0, cpu)")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    
    args = parser.parse_args()
    train_model(
        model_variant=args.model,
        epochs=args.epochs,
        batch_size=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        patience=args.patience
    )
