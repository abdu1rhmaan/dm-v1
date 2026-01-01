from dataclasses import dataclass
from uuid import uuid4
from .task_status import TaskStatus


@dataclass
class DownloadTask:
    id: str
    url: str
    status: TaskStatus
    downloaded: int = 0
    total: int | None = None
    resumable: bool = True  # Whether the download supports resume (HTTP Range requests)
    capability_checked: bool = False  # Whether resumability has been checked
    queue_order: int = 0  # Position in the download queue (1-based)

    @staticmethod
    def create(url: str) -> "DownloadTask":
        return DownloadTask(
            id=str(uuid4()),
            url=url,
            status=TaskStatus.PENDING,
            resumable=True,
            capability_checked=False,
            queue_order=0  # Will be set by the repository when added
        )
