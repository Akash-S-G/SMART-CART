from pydantic import BaseModel
from typing import Dict, Any, List

class ProviderMetadata(BaseModel):
    name: str
    version: str
    capabilities: Dict[str, Any]

class ProductCandidate(BaseModel):
    product_id: str
    name: str
    score: float
    source: str  # e.g., 'barcode', 'ocr', 'embedding'
    metadata: Dict[str, Any] = {}
