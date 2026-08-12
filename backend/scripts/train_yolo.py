from __future__ import annotations

import shutil
import sys
from pathlib import Path
from ultralytics import YOLO


def main():
    print(">>> SmartCart AI - Neural YOLO Training Pipeline (From Scratch)")

    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent
    root_dir = backend_dir.parent

    # Use the larger combined dataset (DB images + vision factory images)
    dataset_yaml = (
        root_dir
        / "vision-dataset-factory"
        / "storage"
        / "exports"
        / "combined_groceries"
        / "data.yaml"
    )

    if not dataset_yaml.exists():
        print(f"[ERROR] Dataset configuration not found at {dataset_yaml}")
        print("[info] Run scripts/prepare_dataset.py first to build the combined dataset.")
        return 1

    print(f"[info] Dataset: {dataset_yaml}")
    
    # Check for existing pretrained weights for transfer learning
    pretrained_weights = backend_dir / "models" / "yolo11n.pt"
    if not pretrained_weights.exists():
        pretrained_weights = backend_dir / "yolo11n.pt"
        
    if pretrained_weights.exists():
        print(f"[info] Initializing YOLO11n with pretrained weights from {pretrained_weights}...")
        model = YOLO(str(pretrained_weights))
    else:
        print("[info] Initializing YOLO11n with standard pretrained weights (yolo11n.pt)...")
        model = YOLO("yolo11n.pt")

    print("[info] Starting training on local DB products dataset (15 epochs)...")
    model.train(
        data=str(dataset_yaml),
        epochs=15,
        imgsz=640,
        device="cpu",
        batch=8,
        project=str(
            root_dir / "vision-dataset-factory" / "storage" / "models"
        ),
        name="combined_groceries_run",
        exist_ok=True,
        patience=5,
        lr0=0.01,
        lrf=0.01,
        warmup_epochs=2,
        close_mosaic=3,
    )

    print(">>> Training complete! Copying best weights to production folders...")
    best_weights = (
        root_dir
        / "vision-dataset-factory"
        / "storage"
        / "models"
        / "combined_groceries_run"
        / "weights"
        / "best.pt"
    )

    if best_weights.exists():
        for dest in [
            backend_dir / "models" / "yolo11n.pt",
            backend_dir / "yolo11n.pt",
            root_dir / "vision-dataset-factory" / "yolo11n.pt",
        ]:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(best_weights, dest)
            print(f"[done] Updated production model weights at: {dest}")
    else:
        print("[ERROR] Trained weights file best.pt not found!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
