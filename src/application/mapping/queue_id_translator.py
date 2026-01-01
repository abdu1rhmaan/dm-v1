from typing import Dict, List
from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from domain.entities.download_task import DownloadTask


class QueueIdTranslator:
    """
    Translates between user-facing queue IDs (1, 2, 3, ...) and internal UUIDs.
    This maintains clean separation between UI and internal identifiers.
    """
    
    def __init__(self, repo: TaskRepository):
        self.repo = repo
    
    def get_all_tasks_with_queue_ids(self, status: TaskStatus | None = None) -> Dict[int, str]:
        """
        Get a mapping of queue IDs to UUIDs for all tasks.
        Queue IDs are based on the persistent queue_order field.
        """
        tasks = self.repo.list_by_queue_order()  # Use queue order directly
        if status:
            tasks = [task for task in tasks if task.status == status]
        
        queue_id_to_uuid = {}
        for task in tasks:
            if task.queue_order > 0:  # Only include tasks with valid queue order
                queue_id_to_uuid[task.queue_order] = task.id
        
        return queue_id_to_uuid
    
    def get_uuid_from_queue_id(self, queue_id: int) -> str | None:
        """
        Translate a queue ID to an internal UUID.
        Returns None if the queue ID is invalid or out of range.
        """
        # Use the direct method instead of getting all tasks
        task = self.repo.get_by_queue_order(queue_id)
        return task.id if task else None
    
    def get_queue_id_from_uuid(self, uuid: str) -> int | None:
        """
        Translate an internal UUID to a queue ID.
        Returns None if the UUID is not found.
        """
        task = self.repo.get(uuid)
        if task:
            return task.queue_order
        return None