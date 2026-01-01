from domain.entities.download_task import DownloadTask
from domain.entities.task_status import TaskStatus
from application.events.task_events import TaskEventListener
from application.use_cases.archive_service import ArchiveService


class ArchiveTaskListener(TaskEventListener):
    """Listener that archives tasks when they finish."""
    
    def __init__(self, archive_service: ArchiveService):
        self.archive_service = archive_service
    
    def on_task_finished(self, task: DownloadTask):
        """Archive the task if it's completed or failed."""
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            try:
                self.archive_service.archive_task(task.id)
            except Exception:
                # If archiving fails, just continue
                print(f"Warning: Could not archive task {task.id}")