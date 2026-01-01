from domain.repositories.task_repository import TaskRepository
from domain.entities.task_status import TaskStatus


class QueueManagementService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def move_up(self, queue_id: int):
        """
        Move a task up in the queue (swap with the task above).
        """
        if queue_id <= 1:
            raise ValueError("Cannot move task up beyond the top of the queue")
        
        # Swap with the task at queue_id - 1
        self.repo.swap_queue_orders(queue_id, queue_id - 1)
        # Normalize queue orders to ensure they are sequential
        self.repo.normalize_queue_order()

    def move_down(self, queue_id: int):
        """
        Move a task down in the queue (swap with the task below).
        """
        # Get all tasks to determine the max queue order
        all_tasks = self.repo.list_by_queue_order()
        max_order = len(all_tasks) if all_tasks else 0
        
        if queue_id >= max_order:
            raise ValueError("Cannot move task down beyond the bottom of the queue")
        
        # Swap with the task at queue_id + 1
        self.repo.swap_queue_orders(queue_id, queue_id + 1)
        # Normalize queue orders to ensure they are sequential
        self.repo.normalize_queue_order()

    def swap(self, queue_id1: int, queue_id2: int):
        """
        Swap two tasks in the queue.
        """
        # Get all tasks to determine the max queue order
        all_tasks = self.repo.list_by_queue_order()
        max_order = len(all_tasks) if all_tasks else 0
        
        if queue_id1 < 1 or queue_id1 > max_order or queue_id2 < 1 or queue_id2 > max_order:
            raise ValueError(f"Queue IDs must be between 1 and {max_order}")
        
        if queue_id1 == queue_id2:
            return  # Nothing to swap
        
        self.repo.swap_queue_orders(queue_id1, queue_id2)
        # Normalize queue orders to ensure they are sequential
        self.repo.normalize_queue_order()