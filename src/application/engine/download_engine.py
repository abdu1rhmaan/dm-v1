from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.download.download_execution_service import DownloadExecutionService
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


import time

class DownloadEngine:
    """
    The authoritative component responsible for download task lifecycle management.
    This is the single source of truth for task execution decisions and status transitions.
    """
    
    def __init__(self, repo: TaskRepository, download_execution_service: DownloadExecutionService, event_manager=None, max_parallel_downloads=1):
        self.repo = repo
        self.download_execution_service = download_execution_service
        self.event_manager = event_manager
        self._pause_flags = {}  # Track pause flags per task
        self._running = False  # Engine loop running state
        self._stop_requested = False  # Stop flag for engine loop
        self._max_parallel_downloads = max_parallel_downloads  # Maximum number of concurrent downloads
        self._active_downloads = set()  # Track currently active downloads
        self._active_downloads_lock = threading.Lock()  # Lock for thread-safe access to active downloads
    
    def _set_pause_flag(self, task_id: str, should_pause: bool):
        self._pause_flags[task_id] = should_pause
    
    def _get_pause_flag(self, task_id: str) -> bool:
        return self._pause_flags.get(task_id, False)
    
    def start(self):
        """
        Start the engine loop to continuously manage task lifecycle.
        """
        if self._running:
            return  # Already running
        
        self._running = True
        self._stop_requested = False
        
        # Run the engine loop
        self._run_engine_loop()
    
    def stop(self):
        """
        Stop the engine loop.
        """
        self._stop_requested = True
        self._running = False
    
    def _run_engine_loop(self):
        """
        The main engine loop that continuously checks repository state
        and decides what to run next.
        """
        while self._running and not self._stop_requested:
            try:
                # Get currently downloading tasks
                downloading_tasks = self.repo.list(status=TaskStatus.DOWNLOADING)
                
                # Get pending tasks ordered by queue order
                all_tasks = self.repo.list_by_queue_order()
                pending_tasks = [task for task in all_tasks if task.status == TaskStatus.PENDING]
                
                # Start new downloads up to the parallel limit
                with self._active_downloads_lock:
                    active_count = len(self._active_downloads)
                
                # Start new downloads if we're below the parallel limit
                for task in pending_tasks:
                    if active_count >= self._max_parallel_downloads:
                        break
                    
                    # Check if this task is already active
                    with self._active_downloads_lock:
                        if task.id not in self._active_downloads:
                            # Start the download
                            self._start_download_task(task.id)
                            active_count += 1
                
                # Sleep briefly to avoid busy-waiting
                time.sleep(0.2)  # 200ms sleep
            
            except Exception as e:
                # Log error but continue running the loop
                print(f"Error in engine loop: {e}")
                time.sleep(1)  # Wait longer on error
            
            # Check if we're in multi-progress mode and there are no more active downloads
            if self._max_parallel_downloads > 1:
                with self._active_downloads_lock:
                    if len(self._active_downloads) == 0:
                        # No more active downloads, finish the multi-progress manager
                        from application.progress.progress_manager_registry import progress_manager_registry
                        multi_manager = progress_manager_registry.get_multi_progress_manager()
                        if multi_manager:
                            multi_manager.finish()
    
    def _start_download_task(self, task_id: str):
        """
        Start a download task in a separate thread.
        """
        # Add to active downloads
        with self._active_downloads_lock:
            self._active_downloads.add(task_id)
        
        # Execute the task in a separate thread
        def run_task():
            try:
                self.execute_task(task_id)
            finally:
                # Remove from active downloads when done
                with self._active_downloads_lock:
                    self._active_downloads.discard(task_id)
        
        # Start the task in a thread
        task_thread = threading.Thread(target=run_task, daemon=True)
        task_thread.start()
    
    def is_running(self) -> bool:
        """
        Check if the engine loop is currently running.
        """
        return self._running
    
    def pause_task(self, task_id: str):
        """
        Pause a download task.
        This is the ONLY method allowed to transition task status to PAUSED.
        """
        # Get the task from repository
        task = self.repo.get(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Validate that the task is in a valid state to be paused
        if task.status != TaskStatus.DOWNLOADING:
            raise ValueError(f"Task must be in DOWNLOADING state to pause, current status: {task.status.value}")
        
        # Set the pause flag for this task
        self._set_pause_flag(task_id, True)
        
        # Update task status to PAUSED - THIS IS THE ONLY PLACE WHERE THIS HAPPENS
        task.status = TaskStatus.PAUSED
        self.repo.update(task)
    
    def resume_task(self, task_id: str):
        """
        Resume a download task that was paused.
        """
        # Get the task from repository
        task = self.repo.get(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Validate that the task is in a valid state to be resumed
        if task.status != TaskStatus.PAUSED:
            raise ValueError(f"Task must be in PAUSED state to resume, current status: {task.status.value}")
        
        # Clear the pause flag before resuming the download
        self._set_pause_flag(task_id, False)
        
        # Update task status to DOWNLOADING
        task.status = TaskStatus.DOWNLOADING
        self.repo.update(task)
        
        # Execute the actual download through the execution service
        self.download_execution_service.execute(task_id)

    def execute_task(self, task_id: str):
        """
        Execute a single download task with proper state management.
        This is the ONLY method allowed to transition task status to DOWNLOADING.
        """
        # Get the task from repository
        task = self.repo.get(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Validate that the task is in a valid state to be downloaded
        if task.status not in [TaskStatus.PENDING, TaskStatus.PAUSED]:
            raise ValueError(f"Task must be in PENDING or PAUSED state to start download, current status: {task.status.value}")
        
        # Clear the pause flag before starting the download
        self._set_pause_flag(task_id, False)
        
        # Update task status to DOWNLOADING - THIS IS THE ONLY PLACE WHERE THIS HAPPENS
        task.status = TaskStatus.DOWNLOADING
        self.repo.update(task)
        
        try:
            # Define a pause check function that the execution service can call
            def pause_check():
                return self._get_pause_flag(task_id)
                    
            # Execute the actual download through the execution service
            # The execution service will handle the mechanics but this engine
            # manages the lifecycle and status transitions
            self.download_execution_service.execute(task_id, pause_check=pause_check)
                    
            # Refresh the task to check if it was paused
            task = self.repo.get(task_id)
            if task and task.status == TaskStatus.PAUSED:
                # If the task was paused during execution, don't change status to COMPLETED
                return
                    
            # Update status to COMPLETED on successful execution
            if task:
                task.status = TaskStatus.COMPLETED
                self.repo.update(task)
                
                # Notify listeners that task is finished
                if hasattr(self, 'event_manager') and self.event_manager:
                    self.event_manager.notify_task_finished(task)
            
            # Check if we're in multi-progress mode and there are no more active downloads
            if self._max_parallel_downloads > 1:
                with self._active_downloads_lock:
                    if len(self._active_downloads) == 0:
                        # No more active downloads, finish the multi-progress manager
                        from application.progress.progress_manager_registry import progress_manager_registry
                        multi_manager = progress_manager_registry.get_multi_progress_manager()
                        if multi_manager:
                            multi_manager.finish()
            
        except Exception as e:
            # If there's an unexpected error during execution, mark as FAILED
            task = self.repo.get(task_id)  # Refresh the task
            if task:  # Check if task still exists
                task.status = TaskStatus.FAILED
                self.repo.update(task)
                
                # Notify listeners that task is finished
                if hasattr(self, 'event_manager') and self.event_manager:
                    self.event_manager.notify_task_finished(task)
            
            # Check if we're in multi-progress mode and there are no more active downloads
            if self._max_parallel_downloads > 1:
                with self._active_downloads_lock:
                    if len(self._active_downloads) == 0:
                        # No more active downloads, finish the multi-progress manager
                        from application.progress.progress_manager_registry import progress_manager_registry
                        multi_manager = progress_manager_registry.get_multi_progress_manager()
                        if multi_manager:
                            multi_manager.finish()
            
            raise e

    def execute_pending_downloads(self):
        """
        Execute all tasks that are in PENDING or PAUSED status.
        This method centralizes the decision of which tasks to run.
        """
        # Execute pending tasks in queue order
        all_tasks = self.repo.list_by_queue_order()
        pending_tasks = [task for task in all_tasks if task.status == TaskStatus.PENDING]
        
        # Execute up to max_parallel_downloads tasks concurrently
        with ThreadPoolExecutor(max_workers=self._max_parallel_downloads) as executor:
            futures = []
            for task in pending_tasks:
                if len(futures) >= self._max_parallel_downloads:
                    break
                try:
                    # Submit the task for execution
                    future = executor.submit(self.execute_task, task.id)
                    futures.append(future)
                except Exception as e:
                    # Log the error but continue with other tasks
                    print(f"Error submitting download for task {task.id}: {e}")
            
            # Wait for all submitted tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()  # This will re-raise any exception from the task
                except Exception as e:
                    print(f"Error in submitted task: {e}")
        
        # Execute paused tasks (resume them)
        paused_tasks = [task for task in all_tasks if task.status == TaskStatus.PAUSED]
        
        for task in paused_tasks:
            try:
                # Clear the pause flag before resuming
                self._set_pause_flag(task.id, False)
                # Execute each paused task individually (resume)
                self.execute_task(task.id)
            except Exception as e:
                # Log the error but continue with other tasks
                print(f"Error resuming download for task {task.id}: {e}")
        
        # If we're in multi-progress mode, finish the multi-progress manager
        if self._max_parallel_downloads > 1:
            from application.progress.progress_manager_registry import progress_manager_registry
            multi_manager = progress_manager_registry.get_multi_progress_manager()
            if multi_manager:
                multi_manager.finish()