from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.download_task import DownloadTask
from domain.entities.task_status import TaskStatus


class TaskRepository(ABC):

    @abstractmethod
    def add(self, task: DownloadTask): ...

    @abstractmethod
    def update(self, task: DownloadTask): ...

    @abstractmethod
    def get(self, task_id: str) -> Optional[DownloadTask]: ...

    @abstractmethod
    def list(self, status: Optional[TaskStatus] = None) -> List[DownloadTask]: ...

    @abstractmethod
    def delete(self, task_id: str): ...
    
    @abstractmethod
    def get_by_queue_order(self, queue_order: int) -> Optional[DownloadTask]: ...
    
    @abstractmethod
    def swap_queue_orders(self, order1: int, order2: int): ...
    
    @abstractmethod
    def normalize_queue_order(self): ...
    
    @abstractmethod
    def list_by_queue_order(self) -> List[DownloadTask]: ...
    
    @abstractmethod
    def archive_task(self, task_id: str): ...
    
    @abstractmethod
    def list_archive(self) -> List[DownloadTask]: ...
    
    @abstractmethod
    def get_from_archive(self, task_id: str) -> Optional[DownloadTask]: ...
