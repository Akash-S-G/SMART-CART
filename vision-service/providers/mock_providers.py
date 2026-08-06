from typing import List, Tuple, Optional, Any, Dict
import numpy as np

from interfaces.detector import DetectorInterface
from interfaces.ocr import OCRInterface
from interfaces.barcode import BarcodeInterface
from interfaces.embedder import EmbedderInterface
from interfaces.retriever import RetrieverInterface
from core.models import ProviderMetadata
from core.context import Detection

class MockDetector(DetectorInterface):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="mock_detector", version="1.0", capabilities={})
        
    def detect_batch(self, images: List[Any]) -> List[List[Detection]]:
        # Return one mock detection per image
        return [[Detection(bbox=[0, 0, 100, 100], confidence=0.9, class_name="product")] for _ in images]

class MockOCR(OCRInterface):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="mock_ocr", version="1.0", capabilities={})
        
    def extract(self, image: Any) -> Tuple[str, float]:
        if getattr(image, "ocr_text", None):
            return image.ocr_text, 0.95
        return "MAGGI MASALA", 0.95

class MockBarcode(BarcodeInterface):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="mock_barcode", version="1.0", capabilities={})
        
    def decode(self, image: Any) -> Optional[str]:
        if getattr(image, "barcode", None):
            return image.barcode
        return "8901058002316"

class MockEmbedder(EmbedderInterface):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="mock_embedder", version="1.0", capabilities={})
        
    def encode(self, image: Any) -> np.ndarray:
        return np.zeros(512)

class MockRetriever(RetrieverInterface):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="mock_retriever", version="1.0", capabilities={})
        
    def search(self, vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        return [{"product_id": "12345", "score": 0.88}]
