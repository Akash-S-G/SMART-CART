"""
SmartCart AI — Standalone ML Vision Microservice
Deployable for FREE to Hugging Face Spaces (Gradio/FastAPI Docker), Modal, or Railway.

Usage:
  uv run uvicorn ml_server:app --port 8001
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import io

app = FastAPI(title="SmartCart AI Vision Microservice", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    # Lazy import to keep startup lightweight
    try:
        from app.ai.model_loader import model_loader
        from app.ai.ocr_engine import ocr_engine
        from app.ai.matcher import match_product

        yolo = model_loader.load_yolo()
        results = yolo(image)

        detections = []
        h, w, _ = image.shape

        for r in results:
            for box in r.boxes:
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                # Extract crop for OCR
                x1, y1, x2, y2 = map(int, coords)
                crop = image[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                ocr_text = ""
                if crop.size > 0:
                    ocr_results = ocr_engine.read_text(crop)
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
        # Graceful fallback response if weights missing
        return {
            "detections": [
                {
                    "bounding_box": {"x": 50, "y": 50, "width": 200, "height": 200},
                    "confidence": 95.0,
                    "ocr_text": "Sample Product",
                    "class_id": 0
                }
            ],
            "imageWidth": 640,
            "imageHeight": 480,
            "status": "mock_fallback",
            "note": str(e)
        }
