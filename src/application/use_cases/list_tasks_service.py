from typing import List
from domain.entities.download_task import DownloadTask
from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.mapping.queue_id_translator import QueueIdTranslator


class ListTasksService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo
        self.translator = QueueIdTranslator(repo)

    def execute(self, status: TaskStatus | None = None) -> List[DownloadTask]:
        """
        List all tasks or filter by status, ordered by queue order.
        
        Args:
            status: Optional status to filter tasks by
            
        Returns:
            List of DownloadTask objects
        """
        if status is None:
            return self.repo.list_by_queue_order()
        else:
            # Filter by status but still maintain queue order
            all_tasks = self.repo.list_by_queue_order()
            return [task for task in all_tasks if task.status == status]
    
    def execute_with_queue_ids(self, status: TaskStatus | None = None) -> List[tuple[int, DownloadTask]]:
        """
        List all tasks with their queue IDs, ordered by queue order.
        
        Args:
            status: Optional status to filter tasks by
            
        Returns:
            List of tuples containing (queue_id, DownloadTask)
        """
        tasks = self.execute(status)  # Use the ordered list
        result = []
        
        for task in tasks:
            queue_id = task.queue_order  # Use queue_order directly
            result.append((queue_id, task))
        
        return result