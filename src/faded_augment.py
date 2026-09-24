import os
import cv2
import numpy as np
from pathlib import Path
import random
import shutil

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
UNIFIED_DIR = WORKSPACE_DIR / "datasets" / "unified"
TRAIN_IMG_DIR = UNIFIED_DIR / "train" / "images"
TRAIN_LBL_DIR = UNIFIED_DIR / "train" / "labels"

USER_IMG1 = Path(r"C:\Users\Akshay\.gemini\antigravity-ide\brain\473585ef-a41c-4fcf-b9f3-804e8261a640\.user_uploaded\media_1787993751706.jpg")
USER_IMG2 = Path(r"C:\Users\Akshay\.gemini\antigravity-ide\brain\473585ef-a41c-4fcf-b9f3-804e8261a640\.user_uploaded\media_1787993751810.jpg")

def apply_faded_effect(img, bboxes):
    """
    Applies synthetic paint wear, fading, erosion, and asphalt blending
    to the zebra crossing regions in the image.
    """
    h, w = img.shape[:2]
    out = img.copy().astype(np.float32)
    
    for bbox in bboxes:
        cls_id, xc, yc, bw, bh = bbox
        if cls_id != 1:  # only apply to zebra_crossing
            continue
            
        x1 = max(0, int((xc - bw / 2) * w))
        y1 = max(0, int((yc - bh / 2) * h))
        x2 = min(w, int((xc + bw / 2) * w))
        y2 = min(h, int((yc + bh / 2) * h))
        
        if x2 <= x1 or y2 <= y1:
            continue
            
        roi = out[y1:y2, x1:x2]
        
        # Estimate asphalt color from surrounding pixels
        asphalt_sample = roi.mean(axis=(0, 1)) * 0.7
        
        # 1. Contrast reduction (fading the paint into asphalt)
        fade_factor = random.uniform(0.35, 0.70)
        roi_faded = roi * (1.0 - fade_factor) + asphalt_sample * fade_factor
        
        # 2. Speckle wear / erosion mask
        rh, rw = roi.shape[:2]
        noise_mask = np.random.uniform(0.5, 1.2, (rh, rw, 1)).astype(np.float32)
        roi_worn = roi_faded * noise_mask
        
        # 3. Patchy erosion (pavement showing through white stripes)
        num_patches = random.randint(3, 8)
        for _ in range(num_patches):
            px = random.randint(0, rw - 1)
            py = random.randint(0, rh - 1)
            prad = random.randint(5, max(6, min(rw, rh) // 6))
            cv2.circle(roi_worn, (px, py), prad, asphalt_sample.tolist(), -1)
        
        # Blend worn ROI back with smoothing
        roi_worn = cv2.GaussianBlur(roi_worn, (3, 3), 0)
        out[y1:y2, x1:x2] = np.clip(roi_worn, 0, 255)
    
    # 4. Overall atmospheric / wet road variations
    if random.random() < 0.4:
        # Darken wet asphalt
        out = out * random.uniform(0.7, 0.9)
    if random.random() < 0.3:
        # Lower overall saturation
        hsv = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= random.uniform(0.5, 0.8)
        out = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        
    return np.clip(out, 0, 255).astype(np.uint8)

def augment_faded_dataset():
    print("=" * 65)
    print("ROAD VISION AI - FADED ZEBRA CROSSING AUGMENTER")
    print("=" * 65)
    
    # 1. Augment existing zebra crossing images with synthetic fading
    zebra_label_files = [f for f in TRAIN_LBL_DIR.glob("zebra_*.txt")]
    print(f"Found {len(zebra_label_files)} zebra crossing training labels.")
    
    # Select ~500 images to create faded variants
    sample_files = random.sample(zebra_label_files, min(500, len(zebra_label_files)))
    created_count = 0
    
    for lbl_file in sample_files:
        img_name = lbl_file.stem + ".jpg"
        img_path = TRAIN_IMG_DIR / img_name
        if not img_path.exists():
            continue
            
        img = cv2.imread(str(img_path))
        if img is None:
            continue
            
        bboxes = []
        with open(lbl_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    bboxes.append([int(parts[0])] + [float(x) for x in parts[1:]])
                    
        if not any(b[0] == 1 for b in bboxes):
            continue
            
        # Apply fading effect
        faded_img = apply_faded_effect(img, bboxes)
        
        # Save new image and label
        new_stem = f"faded_{lbl_file.stem}"
        new_img_path = TRAIN_IMG_DIR / f"{new_stem}.jpg"
        new_lbl_path = TRAIN_LBL_DIR / f"{new_stem}.txt"
        
        cv2.imwrite(str(new_img_path), faded_img)
        shutil.copy2(lbl_file, new_lbl_path)
        created_count += 1
        
    print(f"Generated {created_count} synthetically faded zebra crossing training pairs.")
    
    # 2. Add annotated user faded images with multiple variations
    user_samples = [
        (USER_IMG1, [[1, 0.460, 0.635, 0.460, 0.280]]),  # Image 1 (wet road faded zebra)
        (USER_IMG2, [[1, 0.540, 0.710, 0.820, 0.420]])   # Image 2 (worn urban zebra)
    ]
    
    user_augmented = 0
    for idx, (u_path, u_bboxes) in enumerate(user_samples):
        if not u_path.exists():
            print(f"Warning: User image {u_path} not found!")
            continue
            
        u_img = cv2.imread(str(u_path))
        if u_img is None:
            continue
            
        for var_idx in range(25):  # Create 25 variations per user image
            var_img = u_img.copy()
            var_boxes = [b.copy() for b in u_bboxes]
            
            # Random brightness & contrast
            alpha = random.uniform(0.75, 1.25)
            beta = random.randint(-25, 25)
            var_img = cv2.convertScaleAbs(var_img, alpha=alpha, beta=beta)
            
            # Random horizontal flip
            if random.random() < 0.5:
                var_img = cv2.flip(var_img, 1)
                for b in var_boxes:
                    b[1] = 1.0 - b[1]  # flip xc
                    
            # Random slight crop / zoom
            if random.random() < 0.3:
                vh, vw = var_img.shape[:2]
                dx = int(vw * random.uniform(0.02, 0.08))
                dy = int(vh * random.uniform(0.02, 0.08))
                var_img = cv2.resize(var_img[dy:vh-dy, dx:vw-dx], (vw, vh))
                
            out_stem = f"real_faded_u{idx}_{var_idx}"
            out_img_path = TRAIN_IMG_DIR / f"{out_stem}.jpg"
            out_lbl_path = TRAIN_LBL_DIR / f"{out_stem}.txt"
            
            cv2.imwrite(str(out_img_path), var_img)
            with open(out_lbl_path, "w") as f:
                for b in var_boxes:
                    f.write(f"{b[0]} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f} {b[4]:.6f}\n")
            user_augmented += 1
            
    print(f"Added {user_augmented} real faded road sample augmentations.")
    print("=" * 65)
    print("FADED AUGMENTATION COMPLETE!")
    print("=" * 65)

if __name__ == "__main__":
    augment_faded_dataset()
