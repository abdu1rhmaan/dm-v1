from typing import List, Set


def parse_task_targets(args: List[str]) -> Set[int]:
    """
    Parse task target arguments into a set of queue IDs.
    
    Supported formats:
    - Single ID: ['3'] -> {3}
    - Multiple IDs: ['3', '5', '7'] -> {3, 5, 7}
    - Ranges: ['1-4'] -> {1, 2, 3, 4}
    - Mixed: ['1', '3-6', '9'] -> {1, 3, 4, 5, 6, 9}
    - '--all': Returns empty set to indicate all tasks
    """
    if not args:
        return set()
    
    if '--all' in args:
        return set()  # Empty set indicates "all tasks"
    
    result = set()
    
    for arg in args:
        if '-' in arg:
            # Handle range: '1-4' -> {1, 2, 3, 4}
            try:
                start, end = arg.split('-', 1)
                start_id = int(start)
                end_id = int(end)
                
                if start_id > end_id:
                    start_id, end_id = end_id, start_id
                
                result.update(range(start_id, end_id + 1))
            except ValueError:
                # Invalid range format, skip
                continue
        else:
            # Handle single ID
            try:
                result.add(int(arg))
            except ValueError:
                # Invalid ID format, skip
                continue
    
    return result