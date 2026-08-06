from typing import List, Optional
from core.models import ProductCandidate
from registry.client import ProductRegistryClient

class MockRegistryClient(ProductRegistryClient):
    def lookup_barcode(self, barcode: str) -> Optional[ProductCandidate]:
        if barcode == "8901058002316":
            return ProductCandidate(product_id="12345", name="Maggi Masala", score=1.0, source="barcode")
        return None
        
    def search_keywords(self, text: str) -> List[ProductCandidate]:
        if "MAGGI" in text.upper():
            return [ProductCandidate(product_id="12345", name="Maggi Masala", score=0.9, source="ocr")]
        return []

    def search_embedding(self, candidates: List[dict]) -> List[ProductCandidate]:
        results = []
        for c in candidates:
            if c["product_id"] == "12345":
                results.append(ProductCandidate(product_id="12345", name="Maggi Masala", score=c["score"], source="embedding"))
        return results
