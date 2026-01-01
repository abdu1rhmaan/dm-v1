from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.mapping.queue_id_translator import QueueIdTranslator
from application.engine.download_engine import DownloadEngine


class ExecuteTaskByQueueService:
    def __init__(self, repo: TaskRepository, download_engine: DownloadEngine):
        self.repo = repo
        self.download_engine = download_engine
        self.translator = QueueIdTranslator(repo)

    def execute(self, queue_id: int):
        """
        Execute a single download task using its queue ID.
        
        Args:
            queue_id: Queue ID of the task to execute
            
        Returns:
            The executed DownloadTask object
        """
        # Translate queue ID to UUID
        task_uuid = self.translator.get_uuid_from_queue_id(queue_id)
        if not task_uuid:
            raise ValueError(f"Task with queue ID {queue_id} not found")
        
        # Execute the task using the download engine
        # The engine will handle validation and execution
        self.download_engine.execute_task(task_uuid)