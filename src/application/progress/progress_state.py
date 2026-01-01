import threading
import time
from typing import Optional
from .progress_snapshot import ProgressSnapshot, ProgressPhase


class ProgressState:
    """Mutable progress state that can be safely updated by download workers."""
    
    def __init__(self, queue_id: int, total: Optional[int] = None):
        self._lock = threading.Lock()
        self._queue_id = queue_id
        self._downloaded = 0
        self._total = total
        self._phase = ProgressPhase.CONNECTING
        self._speed_bps = 0.0
        self._eta_seconds = None
        self._last_downloaded = 0
        self._last_time = time.time()
        self._active = True
    
    def update(self, downloaded: int, total: Optional[int] = None):
        """Thread-safe update of progress state."""
        with self._lock:
            # Clamp values to prevent invalid states
            self._downloaded = max(0, downloaded)
            if total is not None:
                self._total = max(0, total)
            
            # Ensure downloaded doesn't exceed total
            if self._total is not None and self._downloaded > self._total:
                self._downloaded = self._total
            
            # Update phase to downloading once we start getting data
            if downloaded > 0 and self._phase == ProgressPhase.CONNECTING:
                self._phase = ProgressPhase.DOWNLOADING
            
            # Calculate speed and ETA
            current_time = time.time()
            time_diff = current_time - self._last_time
            
            if time_diff >= 0.5:  # Update speed every 0.5 seconds to smooth it out
                bytes_diff = downloaded - self._last_downloaded
                if time_diff > 0:
                    self._speed_bps = max(0.0, bytes_diff / time_diff)  # Never negative
                    
                    # Calculate ETA
                    if (self._total and self._total > downloaded and 
                        self._speed_bps > 0):
                        remaining_bytes = self._total - downloaded
                        self._eta_seconds = max(0.0, remaining_bytes / self._speed_bps)
                    else:
                        self._eta_seconds = None
                
                self._last_downloaded = downloaded
                self._last_time = current_time
    
    def set_phase(self, phase: ProgressPhase):
        """Thread-safe phase update."""
        with self._lock:
            self._phase = phase
    
    def set_active(self, active: bool):
        """Set whether progress is active."""
        with self._lock:
            self._active = active
    
    def get_snapshot(self) -> ProgressSnapshot:
        """Create an immutable snapshot of current state for UI thread."""
        with self._lock:
            return ProgressSnapshot(
                queue_id=self._queue_id,
                downloaded=self._downloaded,
                total=self._total,
                phase=self._phase,
                speed_bps=self._speed_bps,
                eta_seconds=self._eta_seconds
            )
    
    @property
    def active(self) -> bool:
        """Whether progress is active."""
        with self._lock:
            return self._active
    
    @property
    def phase(self) -> ProgressPhase:
        """Current phase."""
        with self._lock:
            return self._phase