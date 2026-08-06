from typing import Any
from abc import abstractmethod
from interfaces.base import BaseProvider
import numpy as np

class EmbedderInterface(BaseProvider):
    @abstractmethod
    def encode(self, image: Any) -> np.ndarray:
        """
        Computes a visual embedding for a cropped image.
        Returns:
            A numpy array representing the embedding vector.
        """
        pass
