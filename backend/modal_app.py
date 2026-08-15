"""
SmartCart AI — Modal Serverless ML Deployment Script

Deploy serverless GPU/CPU AI inference to Modal with 1-command:
  modal deploy modal_app.py
"""

import os
import modal
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Define Modal environment image with all ML dependencies
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0", "libgomp1")
    .pip_install(
        "fastapi[standard]",
        "transformers",
        "huggingface-hub",
        "timm",
        "supervision",
        "ultralytics",
        "easyocr",
        "torch",
        "opencv-python-headless",
        "numpy",
        "pillow",
        "pydantic",
        "python-multipart"
    )
    .add_local_file("best.pt", remote_path="/root/best.pt")
)

app = modal.App("smartcart-ai-vision", image=image)
web_app = FastAPI(title="SmartCart AI Vision Grounding DINO + SAM2 Microservice")

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ModelContainer:
    def __init__(self):
        import torch
        from ultralytics import YOLO
        import easyocr
        from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

        print("[info] Modal container starting up. Loading Grounding DINO, YOLO & EasyOCR...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load Grounding DINO
        try:
            dino_id = "IDEA-Research/grounding-dino-tiny"
            self.dino_processor = AutoProcessor.from_pretrained(dino_id)
            self.dino_model = AutoModelForZeroShotObjectDetection.from_pretrained(dino_id).to(self.device)
            self.dino_model.eval()
            print(f"[info] Grounding DINO ({dino_id}) loaded on {self.device}.")
        except Exception as e:
            print(f"[warn] Grounding DINO load failed: {e}")
            self.dino_model = None

        model_path = "/root/best.pt" if os.path.exists("/root/best.pt") else "yolo11n.pt"
        self.yolo = YOLO(model_path)
        self.ocr = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
        print("[info] Models loaded successfully on Modal.")


model_instance = None


def get_models():
    global model_instance
    if model_instance is None:
        model_instance = ModelContainer()
    return model_instance


async def process_prediction(file: UploadFile):
    import cv2
    import numpy as np

    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image payload")

    models = get_models()
    h, w, _ = image.shape
    results = models.yolo(image)

    detections = []
    for r in results:
        for box in r.boxes:
            coords = box.xyxy[0].cpu().numpy().tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            x1, y1, x2, y2 = map(int, coords)
            crop = image[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

            ocr_text = ""
            if crop.size > 0:
                ocr_results = models.ocr.readtext(crop)
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
        "status": "success",
        "detections": detections,
        "imageWidth": w,
        "imageHeight": h,
    }


@web_app.get("/")
@web_app.get("/health")
def health():
    return {"status": "ok", "service": "SmartCart AI Vision Microservice"}


@web_app.post("/")
@web_app.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)):
    return await process_prediction(file)


@app.function(cpu=2.0, memory=2048, min_containers=1)
@modal.asgi_app()
def fastapi_app():
    return web_app
