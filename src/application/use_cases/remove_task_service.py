from domain.repositories.task_repository import TaskRepository
from application.mapping.queue_id_translator import QueueIdTranslator


class RemoveTaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo
        self.translator = QueueIdTranslator(repo)

    def execute(self, task_id: str):
        """
        Remove a task by its UUID.
        
        Args:
            task_id: UUID of the task to remove
        """
        self.repo.delete(task_id)
        # Normalize queue order to keep them sequential
        self.repo.normalize_queue_order()