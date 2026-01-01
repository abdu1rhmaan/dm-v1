import sqlite3
from domain.repositories.task_repository import TaskRepository
from domain.entities.download_task import DownloadTask
from domain.entities.task_status import TaskStatus


class SQLiteTaskRepository(TaskRepository):
    def __init__(self, db_path="dm.db"):
        self.conn = sqlite3.connect(db_path)
        self._init()

    def _init(self):
        # Check if table exists and has the old schema
        cursor = self.conn.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Create table if it doesn't exist
        if not columns:
            self.conn.execute("""
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                url TEXT,
                status TEXT,
                downloaded INTEGER,
                total INTEGER,
                resumable INTEGER DEFAULT 1,
                capability_checked INTEGER DEFAULT 0,
                queue_order INTEGER DEFAULT 0
            )
            """)
        else:
            # Add new columns if they don't exist
            if 'resumable' not in columns:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN resumable INTEGER DEFAULT 1")
            if 'capability_checked' not in columns:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN capability_checked INTEGER DEFAULT 0")
            if 'queue_order' not in columns:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN queue_order INTEGER DEFAULT 0")
        
        # Create archive table if it doesn't exist
        archive_cursor = self.conn.execute("PRAGMA table_info(archive)")
        archive_columns = [row[1] for row in archive_cursor.fetchall()]
        
        if not archive_columns:
            self.conn.execute("""
            CREATE TABLE archive (
                id TEXT PRIMARY KEY,
                url TEXT,
                status TEXT,
                downloaded INTEGER,
                total INTEGER,
                resumable INTEGER,
                capability_checked INTEGER,
                queue_order INTEGER,
                archived_at TEXT
            )
            """)
        
        self.conn.commit()

    def add(self, task: DownloadTask):
        # If queue_order is 0, assign the next available position
        if task.queue_order == 0:
            # Get the highest queue_order and increment
            cursor = self.conn.execute("SELECT MAX(queue_order) FROM tasks")
            max_order = cursor.fetchone()[0]
            task.queue_order = (max_order or 0) + 1
        
        self.conn.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task.id, task.url, task.status.value, task.downloaded, task.total, task.resumable, task.capability_checked, task.queue_order)
        )
        self.conn.commit()

    def update(self, task: DownloadTask):
        self.conn.execute(
            "UPDATE tasks SET status=?, downloaded=?, total=?, resumable=?, capability_checked=?, queue_order=? WHERE id=?",
            (task.status.value, task.downloaded, task.total, task.resumable, task.capability_checked, task.queue_order, task.id)
        )
        self.conn.commit()

    def get(self, task_id):
        r = self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if r is None:
            return None
        # Convert status string back to TaskStatus enum
        status = TaskStatus(r[2])
        return DownloadTask(
            id=r[0],
            url=r[1], 
            status=status,
            downloaded=r[3],
            total=r[4],
            resumable=bool(r[5]),
            capability_checked=bool(r[6]),
            queue_order=r[7]
        )

    def list(self, status=None):
        if status:
            rows = self.conn.execute("SELECT * FROM tasks WHERE status=?", (status.value,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM tasks").fetchall()
        result = []
        for r in rows:
            # Convert status string back to TaskStatus enum
            task_status = TaskStatus(r[2])
            task = DownloadTask(
                id=r[0],
                url=r[1],
                status=task_status,
                downloaded=r[3],
                total=r[4],
                resumable=bool(r[5]),
                capability_checked=bool(r[6]),
                queue_order=r[7]
            )
            result.append(task)
        return result
    
    def delete(self, task_id: str):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        # Normalize queue orders to fix any tasks with queue_order=0
        self._fix_queue_order()
        
        self.conn.commit()
    
    def _fix_queue_order(self):
        """Fix any tasks with queue_order=0 by assigning them proper sequential order."""
        # Check if there are any tasks with queue_order=0
        cursor = self.conn.execute("SELECT COUNT(*) FROM tasks WHERE queue_order=0 OR queue_order IS NULL")
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Get the current max queue_order
            max_cursor = self.conn.execute("SELECT MAX(queue_order) FROM tasks WHERE queue_order > 0")
            max_order = max_cursor.fetchone()[0] or 0
            
            # Update tasks with queue_order=0 to have sequential order starting after max
            rows = self.conn.execute("SELECT id FROM tasks WHERE queue_order=0 OR queue_order IS NULL ORDER BY id").fetchall()
            for i, row in enumerate(rows, start=max_order + 1):
                self.conn.execute("UPDATE tasks SET queue_order=? WHERE id=?", (i, row[0]))
            
            self.conn.commit()
    
    def normalize_queue_order(self):
        """Normalize queue orders to be sequential (1, 2, 3, ...) based on current order."""
        # Get all tasks ordered by current queue_order
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY queue_order").fetchall()
        
        for i, r in enumerate(rows, start=1):
            # Update each task's queue_order to be sequential
            self.conn.execute("UPDATE tasks SET queue_order=? WHERE id=?", (i, r[0]))
        
        self.conn.commit()
    
    def get_by_queue_order(self, queue_order: int):
        """Get a task by its queue order."""
        r = self.conn.execute("SELECT * FROM tasks WHERE queue_order=?", (queue_order,)).fetchone()
        if r is None:
            return None
        # Convert status string back to TaskStatus enum
        status = TaskStatus(r[2])
        return DownloadTask(
            id=r[0],
            url=r[1],
            status=status,
            downloaded=r[3],
            total=r[4],
            resumable=bool(r[5]),
            capability_checked=bool(r[6]),
            queue_order=r[7]
        )
    
    def swap_queue_orders(self, order1: int, order2: int):
        """Swap the queue orders of two tasks."""
        # Get both tasks
        task1 = self.get_by_queue_order(order1)
        task2 = self.get_by_queue_order(order2)
        
        if not task1 or not task2:
            raise ValueError("One or both queue orders not found")
        
        # Swap the queue orders in memory
        task1.queue_order = order2
        task2.queue_order = order1
        
        # Update both tasks in the database
        self.update(task1)
        self.update(task2)
    
    def normalize_queue_order(self):
        """Normalize queue orders to be sequential (1, 2, 3, ...) based on current order."""
        # Get all tasks ordered by current queue_order
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY queue_order").fetchall()
        
        # Always normalize to ensure queue orders start from 1
        # This maintains the current order but assigns sequential numbers
        for i, r in enumerate(rows, start=1):
            # Update each task's queue_order to be sequential starting from 1
            self.conn.execute("UPDATE tasks SET queue_order=? WHERE id=?", (i, r[0]))
        
        self.conn.commit()
    
    def list_by_queue_order(self):
        """List all tasks ordered by queue order."""
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY queue_order").fetchall()
        result = []
        for r in rows:
            # Convert status string back to TaskStatus enum
            task_status = TaskStatus(r[2])
            task = DownloadTask(
                id=r[0],
                url=r[1],
                status=task_status,
                downloaded=r[3],
                total=r[4],
                resumable=bool(r[5]),
                capability_checked=bool(r[6]),
                queue_order=r[7]
            )
            result.append(task)
        return result
    
    def archive_task(self, task_id: str):
        """Move a task from active tasks to archive."""
        # Get the task from active tasks
        task = self.get(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Insert into archive table
        import datetime
        archived_at = datetime.datetime.now().isoformat()
        
        self.conn.execute(
            "INSERT INTO archive VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task.id, task.url, task.status.value, task.downloaded, task.total,
             task.resumable, task.capability_checked, task.queue_order, archived_at)
        )
        
        # Remove from active tasks
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        
        self.conn.commit()
    
    def list_archive(self):
        """List all archived tasks."""
        rows = self.conn.execute("SELECT * FROM archive ORDER BY archived_at DESC").fetchall()
        result = []
        for r in rows:
            # Convert status string back to TaskStatus enum
            task_status = TaskStatus(r[2])
            # Create a DownloadTask object for archived task (with minimal data)
            task = DownloadTask(
                id=r[0],
                url=r[1],
                status=task_status,
                downloaded=r[3],
                total=r[4],
                resumable=bool(r[5]),
                capability_checked=bool(r[6]),
                queue_order=r[7]
            )
            result.append(task)
        return result
    
    def get_from_archive(self, task_id: str):
        """Get a task from archive by ID."""
        r = self.conn.execute("SELECT * FROM archive WHERE id=?", (task_id,)).fetchone()
        if r is None:
            return None
        # Convert status string back to TaskStatus enum
        status = TaskStatus(r[2])
        return DownloadTask(
            id=r[0],
            url=r[1],
            status=status,
            downloaded=r[3],
            total=r[4],
            resumable=bool(r[5]),
            capability_checked=bool(r[6]),
            queue_order=r[7]
        )
