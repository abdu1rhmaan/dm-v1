from infrastructure.persistence.sqlite_repository import SQLiteTaskRepository
from infrastructure.network.http_downloader import HttpDownloader
from infrastructure.fs.file_writer import FileWriter
from application.use_cases.add_task_service import AddTaskService
from application.download.download_execution_service import DownloadExecutionService
from application.use_cases.list_tasks_service import ListTasksService
from application.use_cases.start_task_service import StartTaskService
from application.use_cases.start_task_by_queue_service import StartTaskByQueueService
from application.use_cases.execute_task_service import ExecuteTaskService
from application.use_cases.execute_task_by_queue_service import ExecuteTaskByQueueService
from application.use_cases.remove_task_service import RemoveTaskService
from application.use_cases.remove_task_by_queue_service import RemoveTaskByQueueService
from application.use_cases.pause_all_service import PauseAllService
from application.use_cases.queue_management_service import QueueManagementService
from application.use_cases.archive_service import ArchiveService
from application.engine.background_engine_service import BackgroundEngineService
from application.discovery.page_discovery_service import PageDiscoveryService
from application.grabber.grabber_engine import GrabberEngine
from application.grabber.preview_renderer import PreviewRenderer
from application.hls.hls_engine import HlsEngine
from application.hls.hls_downloader import HlsDownloader
from application.engine.download_engine import DownloadEngine
from application.progress.console_progress_reporter import ConsoleProgressReporter


class Bootstrap:
    def __init__(self):
        self.repo = SQLiteTaskRepository()
        self.downloader = HttpDownloader()
        self.writer = FileWriter()
        self.add_task = AddTaskService(self.repo)
        self.progress_reporter = ConsoleProgressReporter()
        
        # Initialize HLS services first
        self.hls_engine = HlsEngine()
        self.hls_downloader = HlsDownloader()
        
        # Initialize download execution service with HLS downloader
        self.download_execution = DownloadExecutionService(self.repo, self.downloader, self.writer, self.progress_reporter, self.hls_downloader)
        
        # Set up event system for archive functionality
        from application.events.task_events import TaskEventManager
        from application.events.archive_task_listener import ArchiveTaskListener
        from application.use_cases.archive_service import ArchiveService
        
        self.event_manager = TaskEventManager()
        self.archive_service = ArchiveService(self.repo)
        self.archive_listener = ArchiveTaskListener(self.archive_service)
        self.event_manager.add_listener(self.archive_listener)
        
        # Create download engine with event manager
        self.download_engine = DownloadEngine(self.repo, self.download_execution, self.event_manager)
        
        # Background engine uses the same event manager
        self.background_engine = BackgroundEngineService(self.repo, self.download_execution, self.event_manager)
        self.discovery = PageDiscoveryService()
        self.grabber_engine = GrabberEngine()
        self.preview_renderer = PreviewRenderer()
        self.hls_engine = HlsEngine()
        self.hls_downloader = HlsDownloader()
        self.list_tasks = ListTasksService(self.repo)
        self.start_task = StartTaskService(self.repo)
        self.start_task_by_queue = StartTaskByQueueService(self.repo)
        self.execute_task = ExecuteTaskService(self.repo, self.download_engine)
        self.execute_task_by_queue = ExecuteTaskByQueueService(self.repo, self.download_engine)
        self.pause_all = PauseAllService(self.repo, self.download_engine)
        self.queue_management = QueueManagementService(self.repo)
        self.archive = ArchiveService(self.repo)
        self.remove_task = RemoveTaskService(self.repo)
        self.remove_task_by_queue = RemoveTaskByQueueService(self.repo)
