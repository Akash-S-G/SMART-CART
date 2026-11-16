import os
import cv2
import numpy as np
import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import easyocr

app = FastAPI(title="SmartCart AI Vision Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[SmartCart AI] Running on device: {device}")

model_path = "best.pt" if os.path.exists("best.pt") else "yolo11n.pt"
print(f"[SmartCart AI] Loading YOLO model from {model_path}...")
yolo_model = YOLO(model_path)

print("[SmartCart AI] Initializing EasyOCR reader...")
ocr_reader = easyocr.Reader(["en"], gpu=torch.cuda.is_available())
print("[SmartCart AI] Vision models loaded successfully!")


@app.get("/")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "SmartCart AI Vision Microservice",
        "device": device,
        "model": model_path,
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image payload")

    h, w, _ = image.shape
    results = yolo_model(image, conf=0.25, verbose=False)

    detections = []
    for r in results:
        for box in r.boxes:
            coords = box.xyxy[0].cpu().numpy().tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            class_name = r.names.get(cls_id, f"item_{cls_id}")

            x1, y1, x2, y2 = map(int, coords)
            crop = image[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

            ocr_text = ""
            if crop.size > 0:
                try:
                    ocr_results = ocr_reader.readtext(crop)
                    ocr_text = " ".join([text for (_, text, prob) in ocr_results if prob > 0.3])
                except Exception as err:
                    print(f"[SmartCart AI] OCR extraction error: {err}")

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
                "class_name": class_name,
            })

    print(f"[SmartCart AI] Processed image ({w}x{h}) -> Found {len(detections)} detection(s)")
    return {
        "status": "success",
        "detections": detections,
        "imageWidth": w,
        "imageHeight": h,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
