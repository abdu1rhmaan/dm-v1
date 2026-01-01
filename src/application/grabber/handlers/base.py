from abc import ABC, abstractmethod
from application.grabber.grabber_result import GrabberResult, UrlType


class GrabberHandler(ABC):
    """Abstract base class for all grabber handlers."""
    
    @abstractmethod
    def supports(self, url_type: UrlType) -> bool:
        """Check if this handler supports the given URL type."""
        pass
    
    @abstractmethod
    def handle(self, url: str) -> GrabberResult:
        """Handle the URL and return a grabber result."""
        pass