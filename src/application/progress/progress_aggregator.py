import threading
from typing import Dict, List, Optional
from .progress_state import ProgressState
from .progress_snapshot import ProgressSnapshot, ProgressPhase


class ProgressAggregator:
    """Thread-safe aggregator for collecting and computing total progress across all tasks."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._states: Dict[str, 'ProgressState'] = {}  # Maps task_id to ProgressState
        self._active_task_ids: List[str] = []  # Track active task IDs for order
    
    def add_task(self, task_id: str, state: ProgressState):
        """Add a task's progress state to the aggregator."""
        with self._lock:
            self._states[task_id] = state
            if task_id not in self._active_task_ids:
                self._active_task_ids.append(task_id)
    
    def remove_task(self, task_id: str):
        """Remove a task from the aggregator when it's completed."""
        with self._lock:
            if task_id in self._states:
                del self._states[task_id]
            if task_id in self._active_task_ids:
                self._active_task_ids.remove(task_id)
    
    def get_total_snapshot(self) -> ProgressSnapshot:
        """Compute and return a snapshot of the total progress across all active tasks."""
        with self._lock:
            if not self._states:
                # Return empty snapshot if no active tasks
                return ProgressSnapshot(
                    queue_id=0,  # Special ID for TOTAL
                    downloaded=0,
                    total=None,
                    phase=ProgressPhase.DOWNLOADING,
                    speed_bps=0.0,
                    eta_seconds=None
                )
            
            # Collect snapshots from all active states
            snapshots = []
            for task_id in self._active_task_ids:
                if task_id in self._states:
                    snapshots.append(self._states[task_id].get_snapshot())
            
            # Filter out completed tasks (for accurate calculation)
            active_snapshots = [s for s in snapshots if s.phase != ProgressPhase.FINALIZING]
            
            if not active_snapshots:
                # If all tasks are finalizing, return a finalizing snapshot
                return ProgressSnapshot(
                    queue_id=0,
                    downloaded=0,
                    total=0,
                    phase=ProgressPhase.FINALIZING,
                    speed_bps=0.0,
                    eta_seconds=None
                )
            
            # Calculate total progress
            total_downloaded = sum(s.downloaded for s in active_snapshots)
            
            # Only include total if all tasks have a total value
            total_size = None
            if all(s.total is not None for s in active_snapshots):
                total_size = sum(s.total for s in active_snapshots)
            
            # Calculate total speed
            total_speed = sum(s.speed_bps for s in active_snapshots)
            
            # Calculate ETA if we have a total size and speed
            total_eta = None
            if total_size and total_speed > 0:
                remaining = total_size - total_downloaded
                if remaining > 0:
                    total_eta = remaining / total_speed
            
            # Determine the overall phase based on active tasks
            # If any task is connecting, overall is connecting
            # If any task is downloading, overall is downloading (unless connecting)
            # If all tasks are finalizing, overall is finalizing
            phase = ProgressPhase.DOWNLOADING
            has_connecting = any(s.phase == ProgressPhase.CONNECTING for s in active_snapshots)
            all_finalizing = all(s.phase == ProgressPhase.FINALIZING for s in active_snapshots)
            
            if has_connecting:
                phase = ProgressPhase.CONNECTING
            elif all_finalizing:
                phase = ProgressPhase.FINALIZING
            
            return ProgressSnapshot(
                queue_id=0,  # Special ID for TOTAL
                downloaded=total_downloaded,
                total=total_size,
                phase=phase,
                speed_bps=total_speed,
                eta_seconds=total_eta
            )
    
    def get_active_snapshots(self) -> List[ProgressSnapshot]:
        """Get snapshots of all currently active tasks."""
        with self._lock:
            snapshots = []
            for task_id in self._active_task_ids:
                if task_id in self._states:
                    snapshot = self._states[task_id].get_snapshot()
                    # Only include non-finalizing tasks in the active list
                    if snapshot.phase != ProgressPhase.FINALIZING:
                        snapshots.append(snapshot)
            return snapshots
    
    def get_task_snapshot(self, task_id: str) -> Optional[ProgressSnapshot]:
        """Get a snapshot for a specific task."""
        with self._lock:
            if task_id in self._states:
                return self._states[task_id].get_snapshot()
            return None