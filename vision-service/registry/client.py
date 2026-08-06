from typing import List, Optional
from core.models import ProductCandidate

class ProductRegistryClient:
    """
    Client for interacting with the local Product Registry database.
    """
    
    def lookup_barcode(self, barcode: str) -> Optional[ProductCandidate]:
        """Looks up a product by exact barcode match."""
        pass
        
    def search_keywords(self, text: str) -> List[ProductCandidate]:
        """
        Normalizes OCR text, expands aliases, and performs a fuzzy match 
        against the product registry.
        """
        pass

    def search_embedding(self, candidates: List[dict]) -> List[ProductCandidate]:
        """
        Takes raw candidates from the FAISS Retriever and resolves them 
        into ProductCandidate objects with metadata.
        """
        pass
