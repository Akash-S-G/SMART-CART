import pytest
import numpy as np
from PIL import Image
import warnings

# Suppress heavy ML warnings during tests
warnings.filterwarnings("ignore")

from providers.yolo_world import YOLOWorldDetector
from providers.easyocr_reader import EasyOCRReader
from providers.siglip_embedder import SigLIPEmbedder
from providers.faiss_retriever import FAISSRetriever

def get_dummy_image():
    # Create a dummy image (e.g., a simple color block)
    arr = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
    return Image.fromarray(arr)

@pytest.mark.skip(reason="Downloads heavy weights, run manually via script if needed")
def test_real_providers_initialization():
    # This test verifies that the real providers can initialize and run inference without crashing.
    
    img = get_dummy_image()
    
    # 1. Detector
    print("Initializing YOLO-World...")
    detector = YOLOWorldDetector(model_size="yolov8n.pt")
    detections = detector.detect_batch([img])
    assert isinstance(detections, list)
    
    # 2. OCR
    print("Initializing EasyOCR...")
    ocr = EasyOCRReader(gpu=False)
    text, conf = ocr.extract(img)
    assert isinstance(text, str)
    
    # 3. Embeddings
    print("Initializing SigLIP...")
    embedder = SigLIPEmbedder()
    vector = embedder.encode(img)
    assert vector.shape == (768,)
    
    print("All models successfully loaded and ran zero-shot inference!")
    
if __name__ == "__main__":
    test_real_providers_initialization()
