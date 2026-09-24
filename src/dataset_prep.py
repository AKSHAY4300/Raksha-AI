import os
import shutil
import zipfile
from pathlib import Path
from collections import Counter
import json

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
POTHOLE_ZIP = WORKSPACE_DIR / "Pothole.v1-raw.yolov12.zip"
ZEBRA_ZIP = WORKSPACE_DIR / "Zebra crossing.v1i.yolov12.zip"

RAW_DIR = WORKSPACE_DIR / "datasets" / "raw"
UNIFIED_DIR = WORKSPACE_DIR / "datasets" / "unified"

CLASS_NAMES = {
    0: "pothole",
    1: "zebra_crossing"
}

def extract_zip(zip_path: Path, target_dir: Path):
    print(f"Extracting {zip_path.name} to {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(target_dir)
    print(f"Extracted {zip_path.name} successfully.")

def normalize_split_name(dir_name: str) -> str:
    name = dir_name.lower().strip()
    if name in ["val", "valid", "validation"]:
        return "valid"
    if name in ["train", "training"]:
        return "train"
    if name in ["test", "testing"]:
        return "test"
    return name

def process_dataset(raw_dir: Path, prefix: str, class_remap_dict: dict, unified_dir: Path, stats: dict):
    print(f"\nProcessing {prefix} from {raw_dir}...")
    
    for split_candidate in ["train", "valid", "val", "test"]:
        split_dir = raw_dir / split_candidate
        if not split_dir.exists():
            continue
        
        target_split = normalize_split_name(split_candidate)
        dest_img_dir = unified_dir / target_split / "images"
        dest_lbl_dir = unified_dir / target_split / "labels"
        dest_img_dir.mkdir(parents=True, exist_ok=True)
        dest_lbl_dir.mkdir(parents=True, exist_ok=True)
        
        src_img_dir = split_dir / "images" if (split_dir / "images").exists() else split_dir
        src_lbl_dir = split_dir / "labels" if (split_dir / "labels").exists() else split_dir
        
        if not src_img_dir.exists():
            continue
        
        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        image_files = [f for f in src_img_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_extensions]
        
        print(f"  Found {len(image_files)} images in {prefix} -> {split_candidate} (mapping to {target_split})")
        
        for img_path in image_files:
            new_img_stem = f"{prefix}_{img_path.stem}"
            new_img_name = f"{new_img_stem}{img_path.suffix.lower()}"
            dest_img_path = dest_img_dir / new_img_name
            
            # Copy image
            shutil.copy2(img_path, dest_img_path)
            stats[target_split]["images"] += 1
            
            # Process corresponding label
            lbl_candidate = src_lbl_dir / f"{img_path.stem}.txt"
            dest_lbl_path = dest_lbl_dir / f"{new_img_stem}.txt"
            
            new_lines = []
            if lbl_candidate.exists():
                with open(lbl_candidate, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        try:
                            orig_cls = int(parts[0])
                            new_cls = class_remap_dict.get(orig_cls, orig_cls)
                            raw_coords = [float(x) for x in parts[1:]]
                            
                            if len(parts) == 5:
                                # Standard bounding box: [x_center, y_center, width, height]
                                xc = max(0.0, min(1.0, raw_coords[0]))
                                yc = max(0.0, min(1.0, raw_coords[1]))
                                w = max(0.001, min(1.0, raw_coords[2]))
                                h = max(0.001, min(1.0, raw_coords[3]))
                            else:
                                # Polygon segmentation: [x1, y1, x2, y2, ... xn, yn]
                                xs = [max(0.0, min(1.0, x)) for x in raw_coords[0::2]]
                                ys = [max(0.0, min(1.0, y)) for y in raw_coords[1::2]]
                                if not xs or not ys:
                                    continue
                                xmin, xmax = min(xs), max(xs)
                                ymin, ymax = min(ys), max(ys)
                                w = max(0.001, min(1.0, xmax - xmin))
                                h = max(0.001, min(1.0, ymax - ymin))
                                xc = max(0.0, min(1.0, xmin + (xmax - xmin) / 2.0))
                                yc = max(0.0, min(1.0, ymin + (ymax - ymin) / 2.0))
                            
                            if w > 0.001 and h > 0.001:
                                new_lines.append(f"{new_cls} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                                stats[target_split]["classes"][CLASS_NAMES[new_cls]] += 1
                        except (ValueError, KeyError, IndexError):
                            continue
            
            with open(dest_lbl_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            
            stats[target_split]["labels"] += 1

def main():
    print("=" * 60)
    print("ROAD VISION AI - DATASET PREPARATION & UNIFICATION")
    print("=" * 60)
    
    pothole_raw = RAW_DIR / "pothole"
    zebra_raw = RAW_DIR / "zebra_crossing"
    
    if not pothole_raw.exists() or len(list(pothole_raw.glob("*"))) == 0:
        extract_zip(POTHOLE_ZIP, pothole_raw)
    else:
        print("Pothole raw dataset already extracted.")
        
    if not zebra_raw.exists() or len(list(zebra_raw.glob("*"))) == 0:
        extract_zip(ZEBRA_ZIP, zebra_raw)
    else:
        print("Zebra Crossing raw dataset already extracted.")
    
    if UNIFIED_DIR.exists():
        print(f"Cleaning existing unified directory: {UNIFIED_DIR}")
        shutil.rmtree(UNIFIED_DIR)
    UNIFIED_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "train": {"images": 0, "labels": 0, "classes": Counter()},
        "valid": {"images": 0, "labels": 0, "classes": Counter()},
        "test": {"images": 0, "labels": 0, "classes": Counter()}
    }
    
    # Process Pothole (Class 0 -> 0: pothole)
    process_dataset(
        raw_dir=pothole_raw,
        prefix="pothole",
        class_remap_dict={0: 0},
        unified_dir=UNIFIED_DIR,
        stats=stats
    )
    
    # Process Zebra Crossing (Class 0 -> 1: zebra_crossing)
    process_dataset(
        raw_dir=zebra_raw,
        prefix="zebra",
        class_remap_dict={0: 1},
        unified_dir=UNIFIED_DIR,
        stats=stats
    )
    
    # Create data.yaml manually (pure python without external yaml dependency)
    yaml_lines = [
        f"path: {str(UNIFIED_DIR.resolve()).replace(chr(92), '/')}",
        "train: train/images",
        "val: valid/images",
        "test: test/images",
        "",
        "nc: 2",
        "names:",
        "  0: pothole",
        "  1: zebra_crossing",
        ""
    ]
    yaml_path = UNIFIED_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(yaml_lines))
    
    # Save stats json for UI / reporting
    stats_json_path = UNIFIED_DIR / "dataset_stats.json"
    serializable_stats = {
        split: {
            "images": s["images"],
            "labels": s["labels"],
            "classes": dict(s["classes"])
        }
        for split, s in stats.items()
    }
    with open(stats_json_path, "w", encoding="utf-8") as f:
        json.dump(serializable_stats, f, indent=2)
    
    print("\n" + "=" * 60)
    print("UNIFIED DATASET SUMMARY")
    print("=" * 60)
    print(f"Data config written to: {yaml_path}")
    for split in ["train", "valid", "test"]:
        s = stats[split]
        print(f"\n[{split.upper()} SET]")
        print(f"  Images: {s['images']}")
        print(f"  Labels: {s['labels']}")
        print(f"  Objects: {dict(s['classes'])}")
    
    total_imgs = sum(stats[s]["images"] for s in stats)
    total_objs = sum(sum(stats[s]["classes"].values()) for s in stats)
    print(f"\nTOTAL ACROSS ALL SPLITS: {total_imgs} images, {total_objs} labeled bounding boxes.")
    print("=" * 60)

if __name__ == "__main__":
    main()
