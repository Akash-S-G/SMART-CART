from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "models"

UPLOAD_DIR = BASE_DIR / "app" / "static" / "uploads"

MODEL_NAME = "yolo11n.pt"

MODEL_PATH = MODEL_DIR / MODEL_NAME

IMAGE_SIZE = 640

CONFIDENCE_THRESHOLD = 0.50

IOU_THRESHOLD = 0.45

MAX_DETECTIONS = 25

DEVICE = "cpu"

SAVE_UPLOADS = False

SUPPORTED_IMAGE_TYPES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)