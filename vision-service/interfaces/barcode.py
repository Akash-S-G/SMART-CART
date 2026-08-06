from typing import Optional, Any
from abc import abstractmethod
from interfaces.base import BaseProvider

class BarcodeInterface(BaseProvider):
    @abstractmethod
    def decode(self, image: Any) -> Optional[str]:
        """
        Extracts a barcode string from a cropped image.
        Returns:
            Decoded barcode string, or None if no barcode is found.
        """
        pass
