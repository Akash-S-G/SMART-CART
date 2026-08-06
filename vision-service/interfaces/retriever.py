from typing import List, Dict, Any
from abc import abstractmethod
from interfaces.base import BaseProvider
import numpy as np

class RetrieverInterface(BaseProvider):
    @abstractmethod
    def search(self, vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches the vector index for similar embeddings.
        Returns:
            List of dictionaries containing {"product_id": str, "score": float}
        """
        pass
