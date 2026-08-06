from abc import ABC, abstractmethod
from typing import Iterator, Dict

class BasePlugin(ABC):
    """
    Base interface for all dataset acquisition plugins.
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the source (e.g., 'openfoodfacts', 'crawl4ai')"""
        pass

    @abstractmethod
    def discover_images(self, product_family: str, query: str) -> Iterator[Dict[str, str]]:
        """
        Discover images for a given product family and search query.
        
        Args:
            product_family: The canonical name of the product family.
            query: The specific search variation (e.g., 'Parle-G packet').
            
        Yields:
            Dictionary containing:
                - image_url: The URL of the discovered image
                - page_url: The URL of the page where the image was found
                - source: The name of the source (self.source_name)
        """
        pass
