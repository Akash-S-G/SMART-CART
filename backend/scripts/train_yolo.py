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
    print(f"[info] Initializing YOLO11n model with random weights (from scratch)...")
    model = YOLO("yolo11n.yaml")

    print(f"[info] Starting training on combined_groceries dataset (30 epochs)...")
    model.train(
        data=str(dataset_yaml),
        epochs=30,
        imgsz=640,
        device="cpu",
        batch=8,
        project=str(
            root_dir / "vision-dataset-factory" / "storage" / "models"
        ),
        name="combined_groceries_run",
        exist_ok=True,
        patience=10,
        lr0=0.01,
        lrf=0.01,
        warmup_epochs=3,
        close_mosaic=5,
    )

    print(">>> Training complete! Copying best weights to active production folder...")
    best_weights = (
        root_dir
        / "vision-dataset-factory"
        / "storage"
        / "models"
        / "combined_groceries_run"
        / "weights"
        / "best.pt"
    )
    prod_path = backend_dir / "models" / "yolo11n.pt"

    if best_weights.exists():
        shutil.copy2(best_weights, prod_path)
        print(f"[done] Successfully updated production model at: {prod_path}")
    else:
        print("[ERROR] Trained weights file best.pt not found!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
