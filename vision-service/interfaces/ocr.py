from typing import Tuple, Any
from abc import abstractmethod
from interfaces.base import BaseProvider

class OCRInterface(BaseProvider):
    @abstractmethod
    def extract(self, image: Any) -> Tuple[str, float]:
        """
        Extracts text from a cropped image.
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        pass
