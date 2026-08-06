from abc import ABC, abstractmethod
from core.models import ProviderMetadata

class BaseProvider(ABC):
    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        pass
