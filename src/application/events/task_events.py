from typing import Protocol, List
from domain.entities.download_task import DownloadTask


class TaskEventListener(Protocol):
    """Protocol for task event listeners."""
    
    def on_task_finished(self, task: DownloadTask):
        """Called when a task is completed or failed."""
        ...


class TaskEventManager:
    """Simple event manager for task events."""
    
    def __init__(self):
        self._listeners: List[TaskEventListener] = []
    
    def add_listener(self, listener: TaskEventListener):
        """Add a listener to the event manager."""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: TaskEventListener):
        """Remove a listener from the event manager."""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def notify_task_finished(self, task: DownloadTask):
        """Notify all listeners that a task has finished."""
        for listener in self._listeners:
            listener.on_task_finished(task)