import zxingcpp
import numpy as np
from PIL import Image
from typing import Optional, Any
from interfaces.barcode import BarcodeInterface
from core.models import ProviderMetadata

class ZXingReader(BarcodeInterface):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="zxing-cpp", version="3.1.0", capabilities={"formats": "EAN-13, UPC, QR"})
        
    def decode(self, image: Any) -> Optional[str]:
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image = np.array(image)
            
        try:
            # zxingcpp can take a numpy array directly
            results = zxingcpp.read_barcodes(image)
            if results:
                # Return the text of the first found barcode
                return results[0].text
        except Exception as e:
            print(f"ZXing Error: {e}")
            
        return None
