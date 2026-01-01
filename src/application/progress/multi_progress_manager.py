import sys
import time
import shutil
import threading
from typing import Optional, Dict
from .progress_reporter import ProgressReporter
from .progress_state import ProgressState, ProgressPhase
from .progress_aggregator import ProgressAggregator
from .progress_snapshot import ProgressSnapshot


class MultiProgressManager(ProgressReporter):
    """State 2 progress manager for rendering multiple concurrent downloads."""
    
    def __init__(self):
        self._aggregator = ProgressAggregator()
        self._renderer_thread: Optional[threading.Thread] = None
        self._stop_rendering = threading.Event()
        self._render_lock = threading.Lock()
        self._active = False
        self._last_render_time = 0
        self._render_interval = 0.1  # 100ms between renders to prevent excessive updates
        
        # Track completion statistics
        self._start_time = time.time()
        self._completed_tasks_count = 0
        self._total_downloaded_at_completion = 0
    
    def add_task(self, queue_id: int, total_size: Optional[int] = None) -> ProgressState:
        """Add a new task to be tracked and return its ProgressState."""
        state = ProgressState(queue_id, total_size)
        self._aggregator.add_task(str(queue_id), state)
        return state
    
    def remove_task(self, queue_id: int):
        """Remove a completed task from tracking and update completion stats."""
        # Get the task's final snapshot to record its contribution to total download
        task_snapshot = self._aggregator.get_task_snapshot(str(queue_id))
        if task_snapshot:
            self._total_downloaded_at_completion += task_snapshot.downloaded
            self._completed_tasks_count += 1
        
        self._aggregator.remove_task(str(queue_id))
    
    def update(self, downloaded: int, total: int | None):
        """This method should not be called directly for multi-progress.
        Use the individual task states instead."""
        pass  # This is just to satisfy the interface
    
    def finish(self):
        """Stop rendering and clear the progress display."""
        if not self._active:
            return
            
        # Stop the renderer thread
        self._stop_rendering.set()
        
        if self._renderer_thread and self._renderer_thread.is_alive():
            self._renderer_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
        
        # Clear the display
        with self._render_lock:
            self._clear_display()
        
        # Calculate session summary if we had completed tasks
        total_time = time.time() - self._start_time
        if self._completed_tasks_count > 0:
            # Calculate average speed based on total downloaded and total time
            avg_speed_bps = self._total_downloaded_at_completion / total_time if total_time > 0 else 0
            
            # Print session summary
            self.print_session_summary(
                completed_tasks=self._completed_tasks_count,
                total_downloaded=self._total_downloaded_at_completion,
                total_time_seconds=total_time,
                avg_speed_bps=avg_speed_bps
            )
        
        self._active = False
    
    def start_rendering(self):
        """Start the rendering thread."""
        if self._active:
            return
            
        self._active = True
        self._stop_rendering.clear()
        self._renderer_thread = threading.Thread(target=self._render_loop, daemon=True)
        self._renderer_thread.start()
    
    def _render_loop(self):
        """Main rendering loop that runs in a separate thread."""
        while not self._stop_rendering.is_set():
            try:
                current_time = time.time()
                if current_time - self._last_render_time >= self._render_interval:
                    self._render_progress()
                    self._last_render_time = current_time
                time.sleep(0.01)  # Small sleep to prevent busy waiting
            except Exception:
                # If there's an error in rendering, continue the loop
                time.sleep(0.1)
    
    def _render_progress(self):
        """Render the TOTAL and sub-bars progress display."""
        if not self._active:
            return
            
        try:
            # Get the total snapshot and active task snapshots
            total_snapshot = self._aggregator.get_total_snapshot()
            active_snapshots = self._aggregator.get_active_snapshots()
            
            # Build the display lines
            lines = []
            
            # Add TOTAL line
            total_line = self._format_progress_line(total_snapshot, is_total=True)
            lines.append(total_line)
            
            # Add lines for each active task
            for snapshot in active_snapshots:
                task_line = self._format_progress_line(snapshot, is_total=False)
                lines.append(task_line)
            
            # Render all lines atomically
            with self._render_lock:
                self._clear_display()
                self._print_lines(lines)
                
        except Exception:
            # If there's an error during rendering, continue silently
            pass
    
    def _format_progress_line(self, snapshot: ProgressSnapshot, is_total: bool) -> str:
        """Format a progress line according to the required style."""
        # Get terminal width and calculate bar width
        try:
            terminal_width = shutil.get_terminal_size().columns
        except OSError:
            # Fallback for environments that don't support terminal size (like CI)
            terminal_width = 80
            
        # Calculate available space for the bar
        # [ID] | [bar] | XX% | X.X MB/s | ETA XX:XX
        prefix = "[TOTAL]" if is_total else f"[{snapshot.queue_id}]"
        suffix = f" | {snapshot.percentage}% | {snapshot.speed_mbps:.1f} MB/s | ETA {snapshot.eta_formatted}"
        
        # Calculate how much space is available for the progress bar
        used_space = len(prefix) + len(suffix) + 4  # +4 for the spaces and brackets
        max_bar_width = max(10, terminal_width - used_space)  # Minimum bar width of 10
        
        # Calculate bar fill
        if snapshot.total and snapshot.total > 0:
            filled_count = int((snapshot.downloaded / snapshot.total) * max_bar_width)
            filled_count = min(filled_count, max_bar_width)  # Clamp to prevent overflow
        else:
            filled_count = 0
            
        # Create the progress bar
        bar = '#' * filled_count + '.' * (max_bar_width - filled_count)
        
        # Create the progress line
        progress_line = f"{prefix} | [{bar}] {suffix}"
        
        # Ensure the line doesn't exceed terminal width
        if len(progress_line) > terminal_width:
            progress_line = progress_line[:terminal_width]
            
        return progress_line
    
    def _clear_display(self):
        """Clear the entire progress display."""
        # Get number of active lines (TOTAL + active tasks)
        active_snapshots = self._aggregator.get_active_snapshots()
        num_lines = 1 + len(active_snapshots)  # 1 for TOTAL + active task lines
        
        # Move cursor up to the first line and clear each line
        for _ in range(num_lines):
            sys.stdout.write('\033[F')  # Move cursor up one line
            sys.stdout.write('\r')      # Move to beginning of line
            sys.stdout.write(' ' * shutil.get_terminal_size().columns)  # Clear the line
            sys.stdout.write('\r')      # Move back to beginning
        sys.stdout.flush()
    
    def _print_lines(self, lines):
        """Print all progress lines."""
        # First clear the old display
        self._clear_display()
        
        # Print each line
        for line in lines:
            print(line)
        sys.stdout.flush()
    
    def print_session_summary(self, completed_tasks: int, total_downloaded: int, 
                            total_time_seconds: float, avg_speed_bps: float):
        """Print a clean session summary when all downloads are complete."""
        # Clear the progress display first
        self._clear_display()
        
        # Calculate average speed in MB/s
        avg_speed_mbps = avg_speed_bps / (1024 * 1024)
        
        # Format time
        hours = int(total_time_seconds // 3600)
        minutes = int((total_time_seconds % 3600) // 60)
        seconds = int(total_time_seconds % 60)
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Format total downloaded in GB or MB
        if total_downloaded >= 1024 * 1024 * 1024:  # 1GB
            total_downloaded_str = f"{total_downloaded / (1024 * 1024 * 1024):.1f} GB"
        else:
            total_downloaded_str = f"{total_downloaded / (1024 * 1024):.1f} MB"
        
        print(f"\nDownload Session Summary:")
        print(f"- Tasks completed: {completed_tasks}")
        print(f"- Total downloaded: {total_downloaded_str}")
        print(f"- Average speed: {avg_speed_mbps:.1f} MB/s")
        print(f"- Time elapsed: {time_str}")