from typing import List, Any
from abc import abstractmethod
from interfaces.base import BaseProvider
from core.context import Detection

class DetectorInterface(BaseProvider):
    @abstractmethod
    def detect_batch(self, images: List[Any]) -> List[List[Detection]]:
        """
        Takes a batch of full frame images and returns a list of detections for each frame.
        """
        pass
