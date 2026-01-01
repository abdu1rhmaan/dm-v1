from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ProgressPhase(Enum):
    CONNECTING = "connecting"
    DOWNLOADING = "downloading"
    FINALIZING = "finalizing"
    PAUSED = "paused"


@dataclass(frozen=True)  # frozen=True makes it immutable
class ProgressSnapshot:
    """Immutable snapshot of progress state for thread-safe UI rendering."""
    
    queue_id: int
    downloaded: int
    total: Optional[int]
    phase: ProgressPhase
    speed_bps: float  # bytes per second
    eta_seconds: Optional[float]
    
    def __post_init__(self):
        # Clamp values to prevent invalid states
        object.__setattr__(self, 'downloaded', max(0, self.downloaded))
        if self.total is not None:
            object.__setattr__(self, 'downloaded', min(self.downloaded, self.total))
        if self.total is not None:
            object.__setattr__(self, 'total', max(0, self.total))
    
    @property
    def percentage(self) -> int:
        """Calculate percentage, clamped to 100."""
        if self.total is None or self.total <= 0:
            return 0
        pct = int((self.downloaded / self.total) * 100)
        return min(pct, 100)
    
    @property
    def speed_mbps(self) -> float:
        """Convert speed to MB/s."""
        return self.speed_bps / (1024 * 1024)
    
    @property
    def eta_formatted(self) -> str:
        """Format ETA as MM:SS or return '00:00' if not available."""
        if self.eta_seconds is None:
            return "00:00"
        
        minutes = int(self.eta_seconds // 60)
        seconds = int(self.eta_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"