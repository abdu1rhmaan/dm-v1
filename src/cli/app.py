import sys
from cli.bootstrap import Bootstrap
from domain.entities.task_status import TaskStatus


def main():
    bs = Bootstrap()
    if len(sys.argv) < 2:
        print("Usage: dm add <url> (handles files, pages, streams) | dm start <queue_id> | dm start <task_id> | dm start --all | dm pause <queue_id> | dm pause --all | dm list | dm remove <queue_id> | dm queue move <queue_id> up|down | dm queue swap <id1> <id2> | dm archive list | dm archive clone <archive_id> | dm discover <url> [--filter] | dm engine start|stop|status")
        return

    if sys.argv[1] == "add":
        if len(sys.argv) < 3:
            print("Usage: dm add <url>")
            return
        
        try:
            url = sys.argv[2]
            
            # Use the grabber engine to process the URL
            result = bs.grabber_engine.process(url)
            
            # Render preview and get user approval
            approved_items = bs.preview_renderer.render_and_get_approval(result)
            
            # Add approved items to the queue
            for item in approved_items:
                task = bs.add_task.execute(item.url)
                print(f"Added to queue [{task.queue_order}] | id={task.id[:8]} | {item.filename or item.url.split('/')[-1][:30]}")
        
        except Exception as e:
            print(f"Error adding task: {e}")
            import traceback
            traceback.print_exc()
    
    elif sys.argv[1] == "start":
        if len(sys.argv) < 3:
            print("Usage: dm start <task_id|queue_id>")
            return
        try:
            # Check if engine is running
            engine_running = bs.background_engine.is_running()
            
            # Check if it's --all flag to start all pending tasks
            if sys.argv[2] == "--all":
                if engine_running:
                    print("Starting all pending downloads via background engine...")
                    bs.background_engine.execute_pending_downloads()
                else:
                    print("Starting all pending downloads...")
                    bs.download_engine.execute_pending_downloads()
            else:
                # Try to parse as queue ID first (numeric)
                try:
                    queue_id = int(sys.argv[2])
                    print(f"Starting task {queue_id}...")
                    if engine_running:
                        # Get the UUID for the queue ID
                        task_uuid = bs.list_tasks.translator.get_uuid_from_queue_id(queue_id)
                        if not task_uuid:
                            print(f"Error: Task with queue ID {queue_id} not found")
                            return
                        
                        # Check if this is resuming a paused task
                        task = bs.repo.get(task_uuid)
                        if task and task.status == TaskStatus.PAUSED:
                            if task.resumable:
                                print(f"Resuming from byte {task.downloaded}")
                            else:
                                print(f"This download does not support resume. Restarting from beginning.")
                        
                        bs.background_engine.execute_task(task_uuid)
                        print(f"Task {queue_id} enqueued in background engine")
                    else:
                        # Get the task to check if it's resuming
                        task_uuid = bs.list_tasks.translator.get_uuid_from_queue_id(queue_id)
                        if task_uuid:
                            task = bs.repo.get(task_uuid)
                            if task and task.status == TaskStatus.PAUSED:
                                if task.resumable:
                                    print(f"Resuming from byte {task.downloaded}")
                                else:
                                    print(f"This download does not support resume. Restarting from beginning.")
                        bs.execute_task_by_queue.execute(queue_id)
                        print(f"Task {queue_id} completed")
                except ValueError:
                    # If not numeric, treat as UUID
                    task_id = sys.argv[2]
                    print(f"Starting task {task_id[:8]}...")
                    if engine_running:
                        # Check if this is resuming a paused task
                        task = bs.repo.get(task_id)
                        if task and task.status == TaskStatus.PAUSED:
                            if task.resumable:
                                print(f"Resuming from byte {task.downloaded}")
                            else:
                                print(f"This download does not support resume. Restarting from beginning.")
                        bs.background_engine.execute_task(task_id)
                        print(f"Task {task_id[:8]} enqueued in background engine")
                    else:
                        # Check if this is resuming a paused task
                        task = bs.repo.get(task_id)
                        if task and task.status == TaskStatus.PAUSED:
                            if task.resumable:
                                print(f"Resuming from byte {task.downloaded}")
                            else:
                                print(f"This download does not support resume. Restarting from beginning.")
                        bs.execute_task.execute(task_id)
                        print(f"Task {task_id[:8]} completed")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error executing download: {e}")
    
    elif sys.argv[1] == "execute":
        # Internal command to execute pending downloads (simulates background worker)
        if len(sys.argv) >= 3 and sys.argv[2] == "all":
            bs.download_engine.execute_pending_downloads()
            print("Executed all pending downloads")
        else:
            print("Usage: dm execute all")
        
    elif sys.argv[1] == "run":
        # Alias for execute all
        bs.download_engine.execute_pending_downloads()
        print("Executed all pending downloads")
    
    elif sys.argv[1] == "list":
        tasks_with_queue_ids = bs.list_tasks.execute_with_queue_ids()
        if not tasks_with_queue_ids:
            print("No tasks found")
        else:
            for queue_id, task in tasks_with_queue_ids:
                # Determine status icon
                if task.status == TaskStatus.PENDING:
                    icon = "○"  # Circle for pending
                elif task.status == TaskStatus.DOWNLOADING:
                    icon = "▶"  # Triangle for downloading
                elif task.status == TaskStatus.COMPLETED:
                    icon = "✓"  # Checkmark for completed
                elif task.status == TaskStatus.PAUSED:
                    icon = "⏸"  # Pause for paused
                elif task.status == TaskStatus.FAILED:
                    icon = "✗"  # Cross for failed
                else:
                    icon = "?"  # Unknown status
                
                # Format progress
                progress_str = f"{task.downloaded}/{task.total or '?'}"
                if task.total and task.total > 0:
                    percentage = (task.downloaded / task.total) * 100
                    progress_str += f" ({percentage:.1f}%)"
                
                print(f"[{queue_id}] {icon} {task.url.split('/')[-1][:30]}... | {task.status.value} | {progress_str}")
    
    elif sys.argv[1] == "pause":
        if len(sys.argv) < 3:
            print("Usage: dm pause <queue_id> | dm pause --all")
            return
        try:
            if sys.argv[2] == "--all":
                # Pause all downloading tasks
                paused_count = bs.pause_all.execute()
                print(f"Paused {paused_count} downloading tasks")
            else:
                # Try to parse as queue ID first (numeric)
                try:
                    queue_id = int(sys.argv[2])
                    print(f"Pausing task {queue_id}...")
                    # Get the UUID for the queue ID
                    task_uuid = bs.list_tasks.translator.get_uuid_from_queue_id(queue_id)
                    if not task_uuid:
                        print(f"Error: Task with queue ID {queue_id} not found")
                        return
                    
                    # Check if the task is resumable to provide appropriate message
                    task = bs.list_tasks.execute()[queue_id - 1] if queue_id <= len(bs.list_tasks.execute()) else None
                    if task and not task.resumable:
                        print(f"Note: This download does not support resume. If interrupted, it will restart from beginning.")
                    
                    # Alternative method: get task by UUID
                    if not task:
                        task = bs.repo.get(task_uuid)
                        if task and not task.resumable:
                            print(f"Note: This download does not support resume. If interrupted, it will restart from beginning.")
                    
                    bs.download_engine.pause_task(task_uuid)
                    print(f"Task {queue_id} paused")
                except ValueError:
                    print(f"Error: Queue ID must be a number")
        except Exception as e:
            print(f"Error pausing task: {e}")
    
    elif sys.argv[1] == "queue":
        if len(sys.argv) < 4:
            print("Usage: dm queue move <queue_id> up|down | dm queue swap <id1> <id2>")
            return
        
        try:
            if sys.argv[2] == "move":
                queue_id = int(sys.argv[3])
                direction = sys.argv[4]
                
                if direction == "up":
                    bs.queue_management.move_up(queue_id)
                    print(f"Task {queue_id} moved up in queue")
                elif direction == "down":
                    bs.queue_management.move_down(queue_id)
                    print(f"Task {queue_id} moved down in queue")
                else:
                    print("Usage: dm queue move <queue_id> up|down")
            elif sys.argv[2] == "swap":
                if len(sys.argv) < 5:
                    print("Usage: dm queue swap <id1> <id2>")
                    return
                id1 = int(sys.argv[3])
                id2 = int(sys.argv[4])
                bs.queue_management.swap(id1, id2)
                print(f"Tasks {id1} and {id2} swapped in queue")
            else:
                print("Usage: dm queue move <queue_id> up|down | dm queue swap <id1> <id2>")
        except ValueError:
            print(f"Error: Queue IDs must be numbers")
        except Exception as e:
            print(f"Error managing queue: {e}")
    
    elif sys.argv[1] == "archive":
        if len(sys.argv) < 3:
            print("Usage: dm archive list | dm archive clone <archive_id>")
            return
        
        try:
            if sys.argv[2] == "list":
                archived_tasks = bs.archive.list_archive()
                if not archived_tasks:
                    print("No archived tasks")
                else:
                    for i, task in enumerate(archived_tasks):
                        print(f"[{i+1}] {task.url[:50]}... | Status: {task.status.value} | Progress: {task.downloaded}/{task.total or '?'}")
            elif sys.argv[2] == "clone":
                if len(sys.argv) < 4:
                    print("Usage: dm archive clone <archive_id>")
                    return
                archive_id = sys.argv[3]
                new_task = bs.archive.clone_from_archive(archive_id)
                print(f"Archived task cloned as new task at queue position {new_task.queue_order}")
            else:
                print("Usage: dm archive list | dm archive clone <archive_id>")
        except Exception as e:
            print(f"Error managing archive: {e}")
    
    elif sys.argv[1] == "discover":
        if len(sys.argv) < 3:
            print("Usage: dm discover <url> [--filter video,image,audio,archive,iso,custom_ext]")
            return
        
        try:
            url = sys.argv[2]
            
            # Parse filters if provided
            filters = []
            for arg in sys.argv[3:]:
                if arg.startswith("--filter"):
                    filter_list = arg.split("=", 1)
                    if len(filter_list) > 1:
                        filters = [f.strip() for f in filter_list[1].split(",")]
                    else:
                        print("Usage: dm discover <url> [--filter video,image,audio,archive,iso,custom_ext]")
                        return
            
            # Discover links from the page
            result = bs.discovery.discover_from_page(url, filters=filters)
            
            if not result.links:
                print(f"No downloadable links found on the page.")
                return
            
            print(f"Found {result.total_filtered} downloadable files:")
            for i, link in enumerate(result.links, 1):
                # Get file size in human-readable format
                size_str = "? MB"
                if link.file_size:
                    size_mb = link.file_size / (1024 * 1024)
                    size_str = f"{size_mb:.1f} MB"
                
                # Try to extract filename from URL for display
                filename = link.url.split('/')[-1][:30]  # Limit length
                print(f"[{i}] {filename} ({size_str})")
            
            print("\nActions:")
            print("  [A] Add all")
            print("  [S] Select manually")
            print("  [R] Reject")
            
            choice = input("Choose an action: ").strip().upper()
            
            if choice == "A":
                # Add all links
                for link in result.links:
                    task = bs.add_task.execute(link.url)
                    print(f"Added to queue [{task.queue_order}] | id={task.id[:8]} | {link.url.split('/')[-1][:30]}")
            elif choice == "S":
                # Select manually
                selected_indices = input("Enter space-separated numbers to add (e.g., '1 3 5'): ").strip()
                if selected_indices:
                    indices = [int(x) for x in selected_indices.split()]
                    for idx in indices:
                        if 1 <= idx <= len(result.links):
                            link = result.links[idx - 1]
                            task = bs.add_task.execute(link.url)
                            print(f"Added to queue [{task.queue_order}] | id={task.id[:8]} | {link.url.split('/')[-1][:30]}")
            elif choice == "R":
                print("Rejected all links.")
            else:
                print("Invalid choice. No links added.")
        
        except Exception as e:
            print(f"Error discovering links: {e}")
    
    elif sys.argv[1] == "engine":

        if len(sys.argv) < 3:
            print("Usage: dm engine start | dm engine stop | dm engine status")
            return
        
        try:
            if sys.argv[2] == "start":
                if bs.background_engine.is_running():
                    print("Background engine is already running")
                else:
                    bs.background_engine.start()
                    print("Background engine started")
            elif sys.argv[2] == "stop":
                if not bs.background_engine.is_running():
                    print("Background engine is not running")
                else:
                    bs.background_engine.stop()
                    print("Background engine stopped")
            elif sys.argv[2] == "status":
                if bs.background_engine.is_running():
                    print("Background engine is running")
                else:
                    print("Background engine is not running")
            else:
                print("Usage: dm engine start | dm engine stop | dm engine status")
        except Exception as e:
            print(f"Error managing engine: {e}")
    
    elif sys.argv[1] == "remove":

        if len(sys.argv) < 3:
            print("Usage: dm remove <queue_id>")
            return
        try:
            queue_id = int(sys.argv[2])
            bs.remove_task_by_queue.execute(queue_id)
            print(f"Task {queue_id} removed successfully")
        except ValueError:
            print(f"Error: Queue ID must be a number")
        except Exception as e:
            print(f"Error removing task: {e}")
    
    else:
        print("Unknown command. Usage: dm add <url> (handles files, pages, streams) | dm start <queue_id> | dm start <task_id> | dm start --all | dm pause <queue_id> | dm pause --all | dm list | dm remove <queue_id> | dm queue move <queue_id> up|down | dm queue swap <id1> <id2> | dm archive list | dm archive clone <archive_id> | dm discover <url> [--filter] | dm engine start|stop|status")


if __name__ == "__main__":
    main()
