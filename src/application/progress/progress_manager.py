import sys
import time
import shutil
from typing import Optional
from .progress_reporter import ProgressReporter
from .progress_state import ProgressState, ProgressPhase


class ProgressManager(ProgressReporter):
    """Professional single-line progress bar for single download mode."""
    
    def __init__(self, queue_id: int, total_size: Optional[int] = None):
        self._state = ProgressState(queue_id, total_size)
        self.active = False

    def update(self, downloaded: int, total: Optional[int] = None):
        """Update progress with current downloaded bytes and total size."""
        self._state.update(downloaded, total)
        self._render_progress()
        self.active = True

    def finish(self):
        """Clear the progress line when download finishes."""
        self._state.set_active(False)
        if self.active:
            # Clear the entire line using terminal width
            terminal_width = shutil.get_terminal_size().columns
            print("\r" + " " * terminal_width + "\r", end="", flush=True)
        self.active = False

    def _render_progress(self):
        """Render the professional progress bar."""
        # Get immutable snapshot of current state
        snapshot = self._state.get_snapshot()
            
        # Get terminal width and calculate bar width
        try:
            terminal_width = shutil.get_terminal_size().columns
        except OSError:
            # Fallback for environments that don't support terminal size (like CI)
            terminal_width = 80
                
        min_bar_width = 10
        max_bar_width = max(min_bar_width, terminal_width - 50)  # Leave space for other elements
            
        # Calculate bar fill
        if snapshot.total and snapshot.total > 0:
            filled_count = int((snapshot.downloaded / snapshot.total) * max_bar_width)
            filled_count = min(filled_count, max_bar_width)  # Clamp to prevent overflow
        else:
            filled_count = 0
                
        # Create the progress bar
        bar = '#' * filled_count + '.' * (max_bar_width - filled_count)
            
        # Create the progress line
        progress_line = f"[{snapshot.queue_id}] {snapshot.phase.value} |[{bar}]| {snapshot.percentage}% | {snapshot.speed_mbps:.1f} MB/s | ETA {snapshot.eta_formatted}"
            
        # Ensure the line doesn't exceed terminal width
        if len(progress_line) > terminal_width:
            progress_line = progress_line[:terminal_width]
            
        # Print the progress line in place
        print(f"\r{progress_line}", end="", flush=True)