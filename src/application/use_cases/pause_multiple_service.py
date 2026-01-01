from typing import Set
from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.engine.download_engine import DownloadEngine
from application.mapping.queue_id_translator import QueueIdTranslator


class PauseMultipleService:
    def __init__(self, repo: TaskRepository, download_engine: DownloadEngine):
        self.repo = repo
        self.download_engine = download_engine
        self.translator = QueueIdTranslator(repo)

    def pause_tasks(self, queue_ids: Set[int]) -> tuple[Set[int], Set[int]]:
        """
        Pause multiple tasks by queue IDs.
        
        Args:
            queue_ids: Set of queue IDs to pause
            
        Returns:
            tuple of (paused_queue_ids, skipped_queue_ids)
        """
        all_tasks = self.repo.list_by_queue_order()
        queue_id_to_task = {task.queue_order: task for task in all_tasks}
        
        paused_queue_ids = set()
        skipped_queue_ids = set()
        
        for queue_id in queue_ids:
            if queue_id not in queue_id_to_task:
                skipped_queue_ids.add(queue_id)
                continue
            
            task = queue_id_to_task[queue_id]
            
            # Only pause tasks that are currently downloading or pending
            if task.status not in [TaskStatus.DOWNLOADING, TaskStatus.PENDING]:
                skipped_queue_ids.add(queue_id)
                continue
            
            try:
                # Pause the task
                self.download_engine.pause_task(task.id)
                paused_queue_ids.add(queue_id)
            except Exception:
                # If there's an error pausing this specific task, skip it
                skipped_queue_ids.add(queue_id)
        
        return paused_queue_ids, skipped_queue_ids