from domain.entities.download_task import DownloadTask
from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository


class StartTaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def execute(self, task_id: str) -> DownloadTask:
        """
        Prepare a download task for execution by validating its state.
        
        Args:
            task_id: ID of the task to prepare for starting
            
        Returns:
            The validated DownloadTask object
        """
        # Get the task from repository
        task = self.repo.get(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Check if task is in a valid state to start
        if task.status not in [TaskStatus.PENDING, TaskStatus.PAUSED]:
            raise ValueError(f"Cannot start task with status {task.status.value}. Only PENDING or PAUSED tasks can be started.")
        
        # Task is valid to start, return it (status remains PENDING)
        # The actual execution will be handled by DownloadExecutionService
        return task