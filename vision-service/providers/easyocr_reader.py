import easyocr
import numpy as np
from PIL import Image
from typing import Tuple, Any
from interfaces.ocr import OCRInterface
from core.models import ProviderMetadata

class EasyOCRReader(OCRInterface):
    def __init__(self, gpu: bool = False):
        # Load the models into memory once during initialization
        self.reader = easyocr.Reader(['en'], gpu=gpu, verbose=False)
        
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="easyocr", version="1.7.2", capabilities={"languages": ["en"]})
        
    def extract(self, image: Any) -> Tuple[str, float]:
        if isinstance(image, Image.Image):
            image = np.array(image)
            
        try:
            # detail=1 returns list of (bbox, text, prob)
            results = self.reader.readtext(image, detail=1)
            if not results:
                return "", 0.0
                
            # We can concatenate all detected text or just take the highest confidence one.
            # For product recognition, concatenating all text is usually better for fuzzy matching.
            # But we must compute an average or weighted confidence.
            texts = []
            conf_sum = 0.0
            
            for (bbox, text, prob) in results:
                texts.append(text)
                conf_sum += prob
                
            combined_text = " ".join(texts)
            avg_conf = conf_sum / len(results)
            
            return combined_text, avg_conf
        except Exception as e:
            print(f"OCR Error: {e}")
            return "", 0.0
