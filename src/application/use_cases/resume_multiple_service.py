from typing import Set
from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.engine.download_engine import DownloadEngine
from application.mapping.queue_id_translator import QueueIdTranslator


class ResumeMultipleService:
    def __init__(self, repo: TaskRepository, download_engine: DownloadEngine):
        self.repo = repo
        self.download_engine = download_engine
        self.translator = QueueIdTranslator(repo)

    def resume_tasks(self, queue_ids: Set[int]) -> tuple[Set[int], Set[int]]:
        """
        Resume multiple tasks by queue IDs.
        
        Args:
            queue_ids: Set of queue IDs to resume
            
        Returns:
            tuple of (resumed_queue_ids, skipped_queue_ids)
        """
        all_tasks = self.repo.list_by_queue_order()
        queue_id_to_task = {task.queue_order: task for task in all_tasks}
        
        resumed_queue_ids = set()
        skipped_queue_ids = set()
        
        for queue_id in queue_ids:
            if queue_id not in queue_id_to_task:
                skipped_queue_ids.add(queue_id)
                continue
            
            task = queue_id_to_task[queue_id]
            
            # Only resume tasks that are currently paused
            if task.status != TaskStatus.PAUSED:
                skipped_queue_ids.add(queue_id)
                continue
            
            try:
                # Resume the task using the engine's resume_task method
                # This will change the status and start the download again
                self.download_engine.resume_task(task.id)
                resumed_queue_ids.add(queue_id)
            except Exception:
                # If there's an error resuming this specific task, skip it
                skipped_queue_ids.add(queue_id)
        
        return resumed_queue_ids, skipped_queue_ids