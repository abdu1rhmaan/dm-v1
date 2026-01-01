import sys
from .progress_reporter import ProgressReporter

class ConsoleProgressReporter(ProgressReporter):
    """Console-based progress reporter that displays a textual progress bar."""
    
    def __init__(self, width: int = 30):
        self.width = width
        self.current_downloaded = 0
        self.current_total = None
    
    def update(self, downloaded: int, total: int | None):
        """Update the progress bar with current download status."""
        self.current_downloaded = downloaded
        self.current_total = total
        
        # Calculate percentage
        if total and total > 0:
            percentage = int((downloaded / total) * 100)
            # Calculate how many characters should be filled
            filled = int((downloaded / total) * self.width)
            # Create the progress bar
            bar = '#' * filled + '.' * (self.width - filled)
            # Print the progress bar on the same line
            print(f'\r[{bar}] {percentage}%', end='', flush=True)
        else:
            # If total is unknown, show a simple indicator
            print(f'\rDownloading... {downloaded} bytes', end='', flush=True)
    
    def finish(self):
        """Complete the progress display."""
        if self.current_total and self.current_total > 0:
            percentage = 100
            bar = '#' * self.width
            print(f'\r[{bar}] {percentage}%')
        else:
            print(f'\rDownload completed! {self.current_downloaded} bytes downloaded')