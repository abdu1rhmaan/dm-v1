from domain.repositories.task_repository import TaskRepository
from application.mapping.queue_id_translator import QueueIdTranslator
from application.use_cases.remove_task_service import RemoveTaskService


class RemoveTaskByQueueService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo
        self.translator = QueueIdTranslator(repo)
        self.remove_task_service = RemoveTaskService(repo)

    def execute(self, queue_id: int):
        """
        Remove a task using its queue ID.
        
        Args:
            queue_id: Queue ID of the task to remove
        """
        # Translate queue ID to UUID
        task_uuid = self.translator.get_uuid_from_queue_id(queue_id)
        if not task_uuid:
            raise ValueError(f"Task with queue ID {queue_id} not found")
        
        # Remove the task using its UUID
        self.remove_task_service.execute(task_uuid)