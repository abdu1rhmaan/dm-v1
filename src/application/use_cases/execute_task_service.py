from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.engine.download_engine import DownloadEngine


class ExecuteTaskService:
    def __init__(self, repo: TaskRepository, download_engine: DownloadEngine):
        self.repo = repo
        self.download_engine = download_engine

    def execute(self, task_id: str):
        """
        Execute a single download task using its UUID.
        
        Args:
            task_id: UUID of the task to execute
            
        Returns:
            The executed DownloadTask object
        """
        # Execute the task using the download engine
        # The engine will handle validation and execution
        self.download_engine.execute_task(task_id)