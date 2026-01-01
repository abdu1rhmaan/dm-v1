import threading
import time
from typing import Optional
from domain.repositories.task_repository import TaskRepository
from application.engine.download_engine import DownloadEngine


class BackgroundEngineService:
    """Service that manages the background engine loop."""
    
    def __init__(self, repo: TaskRepository, download_execution_service, event_manager=None):
        from application.events.task_events import TaskEventManager
        from application.events.archive_task_listener import ArchiveTaskListener
        from application.use_cases.archive_service import ArchiveService
        
        if event_manager is None:
            # Create a new event manager if none provided
            self.event_manager = TaskEventManager()
            self.archive_service = ArchiveService(repo)
            self.archive_listener = ArchiveTaskListener(self.archive_service)
            self.event_manager.add_listener(self.archive_listener)
        else:
            # Use the provided event manager
            self.event_manager = event_manager
        
        self.download_engine = DownloadEngine(repo, download_execution_service, self.event_manager)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
    
    def start(self):
        """Start the background engine loop."""
        with self._lock:
            if self._running:
                return  # Already running
            
            self._running = True
            self._thread = threading.Thread(target=self._run_engine_loop, daemon=True)
            self._thread.start()
    
    def stop(self):
        """Stop the background engine loop."""
        with self._lock:
            if not self._running:
                return  # Already stopped
            
            self.download_engine.stop()
            self._running = False
    
    def is_running(self) -> bool:
        """Check if the background engine is running."""
        return self._running and self.download_engine.is_running()
    
    def _run_engine_loop(self):
        """Internal method to run the engine loop."""
        self.download_engine.start()
    
    def execute_task(self, task_id: str):
        """Execute a specific task via the background engine."""
        return self.download_engine.execute_task(task_id)
    
    def execute_pending_downloads(self):
        """Execute all pending downloads."""
        return self.download_engine.execute_pending_downloads()