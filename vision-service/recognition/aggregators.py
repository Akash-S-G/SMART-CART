from typing import List, Optional
from core.models import ProductCandidate

class ConfidenceAggregator:
    def aggregate(self, candidates: List[ProductCandidate]) -> Optional[ProductCandidate]:
        """
        Applies weighted rules to merge confidence scores from different sources 
        (Barcode, OCR, Embeddings) referencing the same product_id.
        """
        merged = {}
        for c in candidates:
            if c.product_id not in merged:
                merged[c.product_id] = 0.0
                
            # Weighted rules
            if c.source == 'barcode':
                merged[c.product_id] += (c.score * 1.0)
            elif c.source == 'ocr':
                merged[c.product_id] += (c.score * 0.15)
            elif c.source == 'embedding':
                merged[c.product_id] += (c.score * 0.1)
                
        if not merged:
            return None
            
        # Find best candidate
        best_id = max(merged.items(), key=lambda x: x[1])[0]
        best_score = merged[best_id]
        
        # Return a unified candidate representation
        # (In a real system, we'd pull the full name from the registry again)
        return ProductCandidate(
            product_id=best_id,
            name=f"Product {best_id}", 
            score=best_score,
            source="aggregated"
        )
