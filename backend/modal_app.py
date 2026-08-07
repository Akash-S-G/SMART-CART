"""
SmartCart AI — Modal Serverless ML Deployment Script

Deploy serverless GPU/CPU AI inference to Modal with 1-command:
  modal deploy modal_app.py
"""

import modal
from fastapi import UploadFile, File

# Define Modal environment image with all ML dependencies
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0", "libgomp1")
    .pip_install(
        "fastapi[standard]",
        "ultralytics",
        "easyocr",
        "torch",
        "opencv-python-headless",
        "numpy",
        "pillow",
        "pydantic"
    )
)

app = modal.App("smartcart-ai-vision", image=image)


@app.cls(
    cpu=2.0,
    memory=2048,
    min_containers=1,  # Keeps 1 instance warm for instant responses
)
class SmartCartModel:
    @modal.enter()
    def setup(self):
        import torch
        from ultralytics import YOLO
        import easyocr

        print("[info] Modal container starting up. Loading YOLO & EasyOCR...")
        # Load YOLO model
        self.yolo = YOLO("yolo11n.pt")
        # Load EasyOCR
        self.ocr = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
        print("[info] Models loaded successfully on Modal.")

    @modal.fastapi_endpoint(method="POST")
    async def predict(self, file: UploadFile = File(...)):
        import cv2
        import numpy as np

        if not file:
            return {"status": "error", "message": "No file uploaded"}

        contents = await file.read()

        # Decode image bytes
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {"status": "error", "message": "Invalid image format"}

        h, w, _ = image.shape
        results = self.yolo(image)

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
                    ocr_results = self.ocr.readtext(crop)
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
