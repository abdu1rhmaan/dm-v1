from domain.repositories.task_repository import TaskRepository
from domain.entities.task_status import TaskStatus
from domain.entities.download_task import DownloadTask


class ArchiveService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def archive_task(self, task_id: str):
        """
        Move a completed or failed task to the archive.
        """
        task = self.repo.get(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Only allow archiving completed or failed tasks
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            raise ValueError(f"Only completed or failed tasks can be archived, current status: {task.status.value}")
        
        self.repo.archive_task(task_id)

    def list_archive(self):
        """
        List all archived tasks.
        """
        return self.repo.list_archive()

    def clone_from_archive(self, task_id: str) -> DownloadTask:
        """
        Clone an archived task to create a new pending task.
        """
        archived_task = self.repo.get_from_archive(task_id)
        if not archived_task:
            raise ValueError(f"Archived task with id {task_id} not found")
        
        # Create a new task with the same URL but reset status and progress
        new_task = DownloadTask.create(archived_task.url)
        new_task.status = TaskStatus.PENDING
        new_task.downloaded = 0
        new_task.resumable = True  # Re-evaluate resumability when executed
        new_task.capability_checked = False
        
        # Add the new task to the repository (it will get the next queue position)
        self.repo.add(new_task)
        
        return new_task