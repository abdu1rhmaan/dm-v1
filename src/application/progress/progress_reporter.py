from abc import ABC, abstractmethod

class ProgressReporter(ABC):
    """Abstract interface for progress reporting."""
    
    @abstractmethod
    def update(self, downloaded: int, total: int | None):
        """Update progress with current downloaded bytes and total size."""
        pass
    
    @abstractmethod
    def finish(self):
        """Called when download is complete."""
        pass