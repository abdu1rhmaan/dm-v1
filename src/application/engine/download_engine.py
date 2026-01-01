from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.download.download_execution_service import DownloadExecutionService


import time

class DownloadEngine:
    """
    The authoritative component responsible for download task lifecycle management.
    This is the single source of truth for task execution decisions and status transitions.
    """
    
    def __init__(self, repo: TaskRepository, download_execution_service: DownloadExecutionService, event_manager=None):
        self.repo = repo
        self.download_execution_service = download_execution_service
        self.event_manager = event_manager
        self._pause_flags = {}  # Track pause flags per task
        self._running = False  # Engine loop running state
        self._stop_requested = False  # Stop flag for engine loop
    
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
                # Check if any task is currently DOWNLOADING
                downloading_tasks = self.repo.list(status=TaskStatus.DOWNLOADING)
                
                if not downloading_tasks:
                    # No task is currently downloading, pick next task with status PENDING
                    # Get tasks ordered by queue order
                    all_tasks = self.repo.list_by_queue_order()
                    
                    # Find the first pending task in queue order
                    pending_task = None
                    for task in all_tasks:
                        if task.status == TaskStatus.PENDING:
                            pending_task = task
                            break
                    
                    if pending_task:
                        # Execute the pending task in queue order
                        self.execute_task(pending_task.id)
                    # Note: Paused tasks are resumed explicitly by user commands, not automatically
                
                # Sleep briefly to avoid busy-waiting
                time.sleep(0.2)  # 200ms sleep
            
            except Exception as e:
                # Log error but continue running the loop
                print(f"Error in engine loop: {e}")
                time.sleep(1)  # Wait longer on error
    
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
            
        except Exception as e:
            # If there's an unexpected error during execution, mark as FAILED
            task = self.repo.get(task_id)  # Refresh the task
            if task:  # Check if task still exists
                task.status = TaskStatus.FAILED
                self.repo.update(task)
                
                # Notify listeners that task is finished
                if hasattr(self, 'event_manager') and self.event_manager:
                    self.event_manager.notify_task_finished(task)
            raise e

    def execute_pending_downloads(self):
        """
        Execute all tasks that are in PENDING or PAUSED status.
        This method centralizes the decision of which tasks to run.
        """
        # Execute pending tasks in queue order
        all_tasks = self.repo.list_by_queue_order()
        pending_tasks = [task for task in all_tasks if task.status == TaskStatus.PENDING]
        
        for task in pending_tasks:
            try:
                # Execute each pending task individually
                self.execute_task(task.id)
            except Exception as e:
                # Log the error but continue with other tasks
                print(f"Error executing download for task {task.id}: {e}")
        
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