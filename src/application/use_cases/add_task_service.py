from domain.entities.download_task import DownloadTask
from domain.repositories.task_repository import TaskRepository


class AddTaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def execute(self, url: str) -> DownloadTask:
        """
        Add a new download task at the end of the queue.
        
        Args:
            url: URL to download
            
        Returns:
            The created DownloadTask object
        """
        task = DownloadTask.create(url)
        # The repository will set the queue_order automatically to the next available position
        self.repo.add(task)
        return task
