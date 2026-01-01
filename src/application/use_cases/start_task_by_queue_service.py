from domain.entities.download_task import DownloadTask
from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.mapping.queue_id_translator import QueueIdTranslator


class StartTaskByQueueService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo
        self.translator = QueueIdTranslator(repo)

    def execute(self, queue_id: int) -> DownloadTask:
        """
        Start a download task using its queue ID.
        
        Args:
            queue_id: Queue ID of the task to start
            
        Returns:
            The validated DownloadTask object
        """
        # Translate queue ID to UUID
        task_uuid = self.translator.get_uuid_from_queue_id(queue_id)
        if not task_uuid:
            raise ValueError(f"Task with queue ID {queue_id} not found")
        
        # Get the task from repository
        task = self.repo.get(task_uuid)
        if not task:
            raise ValueError(f"Task with ID {task_uuid} not found")
        
        # Check if task is in a valid state to start
        if task.status not in [TaskStatus.PENDING]:
            raise ValueError(f"Cannot start task with status {task.status.value}. Only PENDING tasks can be started.")
        
        # Task is valid to start, return it (status remains PENDING)
        # The actual execution will be handled by DownloadEngine
        return task