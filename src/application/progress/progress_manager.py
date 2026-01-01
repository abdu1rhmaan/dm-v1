import sys
import time
import shutil
from typing import Optional
from .progress_reporter import ProgressReporter


class ProgressManager(ProgressReporter):
    """Professional single-line progress bar for single download mode."""
    
    def __init__(self, queue_id: int, total_size: Optional[int] = None):
        self.queue_id = queue_id
        self.total_size = total_size
        self.start_time = time.time()
        self.prev_downloaded = 0
        self.prev_time = self.start_time
        self.current_downloaded = 0
        self.last_speed = 0.0
        self.last_eta = "00:00"
        self.active = False

    def update(self, downloaded: int, total: Optional[int] = None):
        """Update progress with current downloaded bytes and total size."""
        self.current_downloaded = downloaded
        if total is not None:
            self.total_size = total
            
        # Calculate speed (MB/s)
        current_time = time.time()
        time_diff = current_time - self.prev_time
        if time_diff >= 0.5:  # Update speed every 0.5 seconds to smooth it out
            bytes_diff = downloaded - self.prev_downloaded
            if time_diff > 0:
                speed_bps = bytes_diff / time_diff
                self.last_speed = speed_bps / (1024 * 1024)  # Convert to MB/s
                
                # Calculate ETA
                if self.total_size and self.total_size > downloaded and self.last_speed > 0:
                    remaining_bytes = self.total_size - downloaded
                    eta_seconds = remaining_bytes / (self.last_speed * 1024 * 1024)
                    eta_minutes = int(eta_seconds // 60)
                    eta_secs = int(eta_seconds % 60)
                    self.last_eta = f"{eta_minutes:02d}:{eta_secs:02d}"
                else:
                    self.last_eta = "00:00"
                    
            self.prev_downloaded = downloaded
            self.prev_time = current_time
        
        self._render_progress()
        self.active = True

    def finish(self):
        """Clear the progress line when download finishes."""
        if self.active:
            # Clear the entire line using terminal width
            terminal_width = shutil.get_terminal_size().columns
            print("\r" + " " * terminal_width + "\r", end="", flush=True)
        self.active = False

    def _render_progress(self):
        """Render the professional progress bar."""
        # Get terminal width and calculate bar width
        terminal_width = shutil.get_terminal_size().columns
        min_bar_width = 10
        max_bar_width = max(min_bar_width, terminal_width - 50)  # Leave space for other elements
        
        # Calculate percentage
        percentage = 0
        if self.total_size and self.total_size > 0:
            percentage = int((self.current_downloaded / self.total_size) * 100)
        
        # Calculate bar fill
        if self.total_size and self.total_size > 0:
            filled_count = int((self.current_downloaded / self.total_size) * max_bar_width)
        else:
            filled_count = 0
            
        # Create the progress bar
        bar = '#' * filled_count + '.' * (max_bar_width - filled_count)
        
        # Format file size
        downloaded_mb = self.current_downloaded / (1024 * 1024)
        
        # Create the progress line
        progress_line = f"[{self.queue_id}] downloading |[{bar}]| {percentage}% | {self.last_speed:.1f} MB/s | ETA {self.last_eta}"
        
        # Ensure the line doesn't exceed terminal width
        if len(progress_line) > terminal_width:
            progress_line = progress_line[:terminal_width]
        
        # Print the progress line in place
        print(f"\r{progress_line}", end="", flush=True)