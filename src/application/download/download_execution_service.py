from typing import Callable
from urllib.parse import urlparse
import os
from domain.entities.download_task import DownloadTask
from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from infrastructure.network.http_downloader import HttpDownloader
from infrastructure.fs.file_writer import FileWriter
from application.progress.progress_reporter import ProgressReporter
from application.progress.console_progress_reporter import ConsoleProgressReporter
from application.progress.progress_manager import ProgressManager
from application.hls.hls_downloader import HlsDownloader
from application.mapping.queue_id_translator import QueueIdTranslator


class DownloadExecutionService:
    def __init__(self, repo: TaskRepository, downloader: HttpDownloader, writer: FileWriter, progress_reporter: ProgressReporter | None = None, hls_downloader: HlsDownloader | None = None):
        self.repo = repo
        self.downloader = downloader
        self.writer = writer
        self.hls_downloader = hls_downloader or HlsDownloader()
        self.progress_reporter = progress_reporter  # This will be overridden per download
        self.queue_translator = QueueIdTranslator(repo)

    def execute(self, task_id: str, pause_check: Callable[[], bool] | None = None):
        # Get the task from repository
        task = self.repo.get(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
                
        # The DownloadEngine is responsible for transitioning to DOWNLOADING state
        # This service only executes the actual download mechanics
        # Validate that the task is in a valid state for execution
        if task.status not in [TaskStatus.DOWNLOADING]:
            raise ValueError(f"Task must be in DOWNLOADING state for execution, current status: {task.status.value}")
                
        # Get the queue ID for this task
        queue_id = self.queue_translator.get_queue_id_from_uuid(task_id)
        if queue_id is None:
            queue_id = 0  # Default to 0 if not found
        
        # Create a ProgressManager for this download
        from application.progress.progress_manager import ProgressManager
        progress_manager = ProgressManager(queue_id, task.total)
        
        # Check if this is an HLS stream (has .m3u8 extension or specific HLS indicators)
        if self._is_hls_stream(task.url):
            # Handle HLS stream download
            return self._execute_hls_download(task, pause_check, progress_manager)
        else:
            # Handle regular HTTP download
            return self._execute_regular_download(task, pause_check, progress_manager)
        
    def _is_hls_stream(self, url: str) -> bool:
        """Check if the URL is an HLS stream."""
        return url.lower().endswith('.m3u8')
        
    def _execute_hls_download(self, task: DownloadTask, pause_check: Callable[[], bool] | None = None, progress_manager=None):
        """Execute HLS stream download."""
        try:
            # Extract filename from URL or use a default
            filename = self._extract_filename_from_url(task.url) or f"hls_{task.id}.mp4"
            if not filename.endswith('.mp4'):
                filename += '.mp4'  # Default to MP4 for HLS streams
                
            output_path = str(self.writer.base / filename)
                
            # Define progress callback
            def progress_callback(downloaded: int, total: int):
                # Update task progress
                task.downloaded = downloaded
                if total is not None and total > 0:
                    task.total = total
                    
                # Update task in repository
                self.repo.update(task)
                    
                # Report progress
                if progress_manager:
                    progress_manager.update(downloaded, total)
                else:
                    # Fallback to the original progress reporter
                    self.progress_reporter.update(downloaded, total) if self.progress_reporter else ConsoleProgressReporter().update(downloaded, total)
                
            # Download the HLS stream
            success = self.hls_downloader.download_variant(
                task.url,
                output_path,
                pause_check=pause_check,
                progress_callback=progress_callback
            )
                
            # Check if download was paused
            if pause_check and pause_check():
                print(f"HLS download paused safely")
                return  # Exit early if paused
                
            # Report completion
            if progress_manager:
                progress_manager.finish()
            else:
                self.progress_reporter.finish() if self.progress_reporter else ConsoleProgressReporter().finish()
                
        except Exception as e:
            # Report completion on error
            if progress_manager:
                progress_manager.finish()
            else:
                self.progress_reporter.finish() if self.progress_reporter else ConsoleProgressReporter().finish()
            raise e
        
    def _execute_regular_download(self, task: DownloadTask, pause_check: Callable[[], bool] | None = None, progress_manager=None):
        """Execute regular HTTP download."""
        try:
            # Check if resumability has been checked, if not, check and update task
            if not task.capability_checked:
                # Get content details to determine if download is resumable
                is_resumable, has_content_length, content_length = self.downloader.get_content_details(task.url)
                    
                # Update task with resumability info
                task.resumable = is_resumable
                task.capability_checked = True
                    
                # Update total if we got it from headers
                if content_length and not task.total:
                    task.total = content_length
                    
                # Save the updated task
                self.repo.update(task)
                    
            # Extract filename from URL or use a default
            filename = self._extract_filename_from_url(task.url) or f"download_{task.id}"
                
            # Check if server supports Range requests
            range_supported = self.downloader.check_range_support(task.url)
                
            # Determine if we should resume based on task.downloaded and .part file existence
            start_byte = 0
            resume = False
                
            # Only allow resume if the server supports range requests AND the task is resumable
            if task.downloaded > 0 and range_supported and task.resumable:
                # Check if .part file exists
                from pathlib import Path
                import os
                tmp_file = self.writer.base / (filename + ".part")
                if tmp_file.exists():
                    file_size = os.path.getsize(tmp_file)
                    if file_size == task.downloaded:  # Only resume if file size matches downloaded amount
                        resume = True
                        start_byte = task.downloaded
                
            # Open file writer with resume option
            self.writer.open(filename, resume=resume)
                
            # Adjust start_byte if resuming but file size differs from task.downloaded
            if resume and start_byte != self.writer.get_current_size():
                start_byte = self.writer.get_current_size()
                task.downloaded = start_byte
                
            # Define the on_chunk callback to handle progress updates
            def on_chunk(chunk: bytes, downloaded: int, total: int):
                # Write chunk to file
                self.writer.write(chunk)
                        
                # Update task progress
                task.downloaded = downloaded
                if total and total > 0:
                    task.total = total
                        
                # Update task in repository
                self.repo.update(task)
                        
                # Report progress
                if progress_manager:
                    progress_manager.update(downloaded, total)
                else:
                    # Fallback to the original progress reporter
                    self.progress_reporter.update(downloaded, total) if self.progress_reporter else ConsoleProgressReporter().update(downloaded, total)
                    
            # Start the download process
            if range_supported and start_byte > 0 and task.resumable:
                # Use Range request to resume download
                self.downloader.download(task.url, on_chunk, start_byte=start_byte, total_size=task.total, pause_check=pause_check)
            elif range_supported and task.resumable:
                # Start from beginning with range support
                self.downloader.download(task.url, on_chunk, start_byte=0, total_size=task.total, pause_check=pause_check)
            else:
                # Fallback to full download without range support
                # Adjust on_chunk to account for start_byte if resuming
                if start_byte > 0:
                    # If we're resuming but server doesn't support range or task is not resumable, start over
                    self.writer.close()
                    self.writer.open(filename, resume=False)  # Start fresh
                    task.downloaded = 0
                    self.repo.update(task)
                    start_byte = 0
                self.downloader.download(task.url, on_chunk, pause_check=pause_check)
                    
            # After download completes OR is paused, check if we need to finalize
            # Check the pause check directly instead of checking repository
            if pause_check and pause_check():
                # If paused, close the file without finalizing
                self.writer.close()
                                    
                # Print message about pause
                if task.total and task.total > 0:
                    print(f"Paused safely at {task.downloaded}/{task.total} bytes")
                else:
                    print(f"Paused safely at {task.downloaded} bytes")
                                    
                # For non-resumable tasks, if paused mid-download, remove the .part file
                # to ensure a clean restart
                if not task.resumable and task.downloaded > 0:
                    from pathlib import Path
                    import os
                    tmp_file = self.writer.base / (filename + ".part")
                    if tmp_file.exists():
                        tmp_file.unlink()  # Remove the .part file
                    # Reset downloaded bytes to 0
                    task.downloaded = 0
                    self.repo.update(task)
                                    
                # Don't report completion if paused
                return  # Exit early if paused
            else:
                # If completed normally, finalize the file
                self.writer.finalize()
                                    
            # Report completion
            if progress_manager:
                progress_manager.finish()
            else:
                self.progress_reporter.finish() if self.progress_reporter else ConsoleProgressReporter().finish()
                
        except Exception as e:
            # Report completion on error
            if progress_manager:
                progress_manager.finish()
            else:
                self.progress_reporter.finish() if self.progress_reporter else ConsoleProgressReporter().finish()
            raise e
    
    def _extract_filename_from_url(self, url: str) -> str | None:
        """Extract filename from URL path or return None if not possible."""
        parsed = urlparse(url)
        path = parsed.path
        filename = os.path.basename(path)
        
        # If there's no filename in the path or it's just a slash, return None
        if not filename or filename == '/':
            return None
        
        # Remove query parameters and fragments if needed
        return filename