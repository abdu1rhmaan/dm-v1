import threading
from typing import Optional
from .multi_progress_manager import MultiProgressManager


class ProgressManagerRegistry:
    """Global registry for progress managers to ensure single renderer."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._multi_progress_manager: Optional[MultiProgressManager] = None
            self._single_progress_manager: Optional['ProgressManager'] = None
            self._state_lock = threading.Lock()
            self._initialized = True
    
    def set_multi_progress_manager(self, manager: MultiProgressManager):
        """Set the multi-progress manager for parallel downloads."""
        with self._state_lock:
            self._multi_progress_manager = manager
    
    def get_multi_progress_manager(self) -> Optional[MultiProgressManager]:
        """Get the multi-progress manager."""
        return self._multi_progress_manager
    
    def set_single_progress_manager(self, manager):
        """Set the single progress manager for single downloads."""
        with self._state_lock:
            self._single_progress_manager = manager
    
    def get_single_progress_manager(self):
        """Get the single progress manager."""
        return self._single_progress_manager
    
    def get_active_manager(self):
        """Get the currently active progress manager (multi takes precedence)."""
        with self._state_lock:
            if self._multi_progress_manager:
                return self._multi_progress_manager
            return self._single_progress_manager
    
    def is_multi_mode(self) -> bool:
        """Check if multi-progress mode is active."""
        with self._state_lock:
            return self._multi_progress_manager is not None


# Global instance
progress_manager_registry = ProgressManagerRegistry()