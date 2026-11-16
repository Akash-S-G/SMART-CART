from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "models"

UPLOAD_DIR = BASE_DIR / "app" / "static" / "uploads"

# Use best.pt — the custom SmartCart model with 718 specific product classes
MODEL_NAME = "best.pt"

MODEL_PATH = MODEL_DIR / MODEL_NAME

IMAGE_SIZE = 640

CONFIDENCE_THRESHOLD = 0.25

IOU_THRESHOLD = 0.45

MAX_DETECTIONS = 12

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