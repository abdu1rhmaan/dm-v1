from abc import ABC, abstractmethod
from .grabber_result import GrabberResult


class GrabberBase(ABC):
    """Base class for all grabbers."""
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this grabber can handle the given URL."""
        pass
    
    @abstractmethod
    def grab(self, url: str) -> GrabberResult:
        """Grab content from the URL and return a result."""
        pass