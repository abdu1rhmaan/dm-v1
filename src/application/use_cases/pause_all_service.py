from domain.entities.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from application.engine.download_engine import DownloadEngine


class PauseAllService:
    def __init__(self, repo: TaskRepository, download_engine: DownloadEngine):
        self.repo = repo
        self.download_engine = download_engine

    def execute(self):
        """
        Pause all downloading tasks.
        """
        # Get all tasks that are currently downloading
        downloading_tasks = self.repo.list(status=TaskStatus.DOWNLOADING)
        
        paused_count = 0
        for task in downloading_tasks:
            try:
                # Pause each downloading task
                self.download_engine.pause_task(task.id)
                paused_count += 1
            except Exception:
                # Continue with other tasks even if one fails
                continue
        
        return paused_count