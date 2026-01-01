from pathlib import Path
import os


class FileWriter:
    def __init__(self, base="downloads"):
        self.base = Path(base)
        self.base.mkdir(exist_ok=True)

    def open(self, name, resume=False, task_id=None):
        # If task_id is provided, make the filename unique to avoid conflicts in parallel downloads
        if task_id:
            unique_name = f"{name}_{task_id}"
        else:
            unique_name = name
        
        self.tmp = self.base / (unique_name + ".part")
        self.final = self.base / name
        
        # Store original name and task_id for use in finalize
        self._original_name = name
        self._task_id = task_id
        
        if resume:
            # If resuming, check if .part file exists and open in append mode
            if self.tmp.exists():
                # Open in append mode to continue writing
                self.fp = open(self.tmp, "ab")
                # Get current file size to know how much is already downloaded
                self.current_size = os.path.getsize(self.tmp)
            else:
                # If .part file doesn't exist but we're trying to resume, start fresh
                self.fp = open(self.tmp, "wb")
                self.current_size = 0
        else:
            # If not resuming, start fresh (old behavior)
            # Remove any existing .part file from previous interrupted download
            if self.tmp.exists():
                self.tmp.unlink()
            
            self.fp = open(self.tmp, "wb")
            self.current_size = 0

    def write(self, data: bytes):
        self.fp.write(data)

    def get_current_size(self):
        """Get the current size of the .part file."""
        if hasattr(self, 'fp') and self.fp and not self.fp.closed:
            # Get current position
            current_pos = self.fp.tell()
            return current_pos
        elif hasattr(self, 'tmp') and self.tmp.exists():
            return os.path.getsize(self.tmp)
        else:
            return 0

    def finalize(self):
        self.fp.close()
        # Remove final file if it already exists (from previous completed download)
        if self.final.exists():
            self.final.unlink()
        self.tmp.rename(self.final)

    def close(self):
        """Close the file without finalizing (for pause functionality)."""
        if hasattr(self, 'fp') and self.fp:
            self.fp.close()
