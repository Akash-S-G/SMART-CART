import faiss
import numpy as np
import json
import os
from typing import List, Dict, Any
from interfaces.retriever import RetrieverInterface
from core.models import ProviderMetadata

class FAISSRetriever(RetrieverInterface):
    def __init__(self, index_path: str, mapping_path: str, dimensions: int = 768):
        self.dimensions = dimensions
        
        # Load or create index
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
        else:
            self.index = faiss.IndexFlatIP(dimensions) # Inner product for cosine similarity
            
        # Load ID mapping (FAISS integer ID -> Product ID string)
        self.mapping = {}
        if os.path.exists(mapping_path):
            with open(mapping_path, "r") as f:
                self.mapping = json.load(f)
                
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="faiss-cpu", version="1.x", capabilities={"index_type": "FlatIP"})
        
    def search(self, vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []
            
        # Ensure shape is (1, d)
        if len(vector.shape) == 1:
            vector = np.expand_dims(vector, axis=0)
            
        # Search
        distances, indices = self.index.search(vector, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: # FAISS returns -1 if there aren't enough items
                continue
                
            faiss_id = str(idx)
            if faiss_id in self.mapping:
                product_id = self.mapping[faiss_id]
                score = float(distances[0][i])
                results.append({"product_id": product_id, "score": score})
                
        return results
