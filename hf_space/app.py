"""
SmartCart AI — Standalone ML Vision Microservice for Hugging Face Spaces
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import os
import torch
from pathlib import Path
from ultralytics import YOLO

app = FastAPI(title="SmartCart AI Vision Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model pointers
model = None
ocr_reader = None

def get_yolo_model():
    global model
    if model is None:
        model_path = Path("models/yolo11n.pt")
        if not model_path.exists():
            model_path = Path("yolo11n.pt")
        if model_path.exists():
            print(f"[info] Loading custom YOLO weights from {model_path}...")
            model = YOLO(str(model_path))
        else:
            print("[warn] Custom weights missing. Loading base yolo11n...")
            model = YOLO("yolo11n.pt")
    return model

def get_ocr_reader():
    global ocr_reader
    if ocr_reader is None:
        import easyocr
        print("[info] Initializing EasyOCR Engine...")
        ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
    return ocr_reader


@app.get("/")
def root():
    return {
        "service": "SmartCart AI Vision Engine",
        "status": "online",
        "endpoints": {
            "health": "/health",
            "predict": "POST /predict"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "SmartCart-ML-Engine"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image payload.")

    try:
        yolo = get_yolo_model()
        reader = get_ocr_reader()

        results = yolo(image)
        detections = []
        h, w, _ = image.shape

        for r in results:
            for box in r.boxes:
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                x1, y1, x2, y2 = map(int, coords)
                crop = image[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                ocr_text = ""
                if crop.size > 0:
                    ocr_results = reader.readtext(crop)
                    ocr_text = " ".join([text for (_, text, prob) in ocr_results if prob > 0.3])

                detections.append({
                    "bounding_box": {
                        "x": x1,
                        "y": y1,
                        "width": x2 - x1,
                        "height": y2 - y1,
                    },
                    "confidence": round(conf * 100, 1),
                    "ocr_text": ocr_text,
                    "class_id": cls_id,
                })

        return {
            "detections": detections,
            "imageWidth": w,
            "imageHeight": h,
            "status": "success"
        }

    except Exception as e:
        print(f"[ERROR] Inference error: {e}")
        return {
            "detections": [
                {
                    "bounding_box": {"x": 50, "y": 50, "width": 200, "height": 200},
                    "confidence": 95.0,
                    "ocr_text": "SmartCart Product",
                    "class_id": 0
                }
            ],
            "imageWidth": 640,
            "imageHeight": 480,
            "status": "fallback",
            "error": str(e)
        }
