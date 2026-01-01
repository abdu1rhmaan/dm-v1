#!/usr/bin/env python3
"""
Test script to validate the new professional progress bar functionality.
"""
import time
from src.application.progress.progress_manager import ProgressManager

def test_progress_bar():
    print("Testing professional progress bar...")
    
    # Create a progress manager for queue ID 23
    progress = ProgressManager(queue_id=23, total_size=1000000)  # 1MB total
    
    # Simulate download progress
    for i in range(0, 101, 5):  # 0% to 100% in 5% increments
        downloaded = int(1000000 * i / 100)
        progress.update(downloaded, 1000000)
        time.sleep(0.1)  # Simulate download time
    
    # Finish the download
    progress.finish()
    print("Test completed!")

if __name__ == "__main__":
    test_progress_bar()