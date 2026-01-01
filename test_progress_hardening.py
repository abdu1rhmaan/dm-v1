#!/usr/bin/env python3
"""
Tests for the hardened progress system (State 1).
"""
import time
import threading
from src.application.progress.progress_snapshot import ProgressSnapshot, ProgressPhase
from src.application.progress.progress_state import ProgressState


def test_snapshot_immutability():
    """Test that ProgressSnapshot is truly immutable."""
    print("Testing snapshot immutability...")
    
    snapshot = ProgressSnapshot(
        queue_id=1,
        downloaded=100,
        total=1000,
        phase=ProgressPhase.DOWNLOADING,
        speed_bps=1000000.0,
        eta_seconds=30.0
    )
    
    # Try to modify the snapshot - this should raise an error
    try:
        snapshot.downloaded = 200
        print("ERROR: Snapshot was mutable!")
        return False
    except AttributeError:
        print("✓ Snapshot is immutable")
    
    print("✓ Snapshot immutability test passed")
    return True


def test_percent_clamping():
    """Test that percentage values are properly clamped."""
    print("Testing percentage clamping...")
    
    # Test normal case
    snapshot1 = ProgressSnapshot(
        queue_id=1,
        downloaded=500,
        total=1000,
        phase=ProgressPhase.DOWNLOADING,
        speed_bps=1000000.0,
        eta_seconds=30.0
    )
    assert snapshot1.percentage == 50, f"Expected 50, got {snapshot1.percentage}"
    
    # Test clamped case (downloaded > total)
    snapshot2 = ProgressSnapshot(
        queue_id=1,
        downloaded=1500,  # More than total
        total=1000,
        phase=ProgressPhase.DOWNLOADING,
        speed_bps=1000000.0,
        eta_seconds=30.0
    )
    assert snapshot2.percentage == 100, f"Expected 100, got {snapshot2.percentage}"
    
    # Test zero total
    snapshot3 = ProgressSnapshot(
        queue_id=1,
        downloaded=500,
        total=0,
        phase=ProgressPhase.DOWNLOADING,
        speed_bps=1000000.0,
        eta_seconds=30.0
    )
    assert snapshot3.percentage == 0, f"Expected 0, got {snapshot3.percentage}"
    
    print("✓ Percentage clamping test passed")
    return True


def test_value_clamping_in_state():
    """Test that ProgressState properly clamps values."""
    print("Testing value clamping in state...")
    
    state = ProgressState(queue_id=1, total=1000)
    
    # Update with values that exceed total
    state.update(downloaded=1500, total=1000)  # downloaded > total
    
    snapshot = state.get_snapshot()
    assert snapshot.downloaded == 1000, f"Expected downloaded to be clamped to 1000, got {snapshot.downloaded}"
    assert snapshot.percentage == 100, f"Expected percentage to be 100, got {snapshot.percentage}"
    
    # Test negative values
    state.update(downloaded=-100, total=-500)
    snapshot = state.get_snapshot()
    assert snapshot.downloaded >= 0, f"Downloaded should be clamped to >= 0, got {snapshot.downloaded}"
    
    print("✓ Value clamping test passed")
    return True


def test_thread_safety():
    """Test thread safety of ProgressState."""
    print("Testing thread safety...")
    
    state = ProgressState(queue_id=1, total=100000)
    
    def update_worker(start_val, increment, iterations):
        for i in range(iterations):
            downloaded = start_val + (i * increment)
            state.update(downloaded, 100000)
            time.sleep(0.001)  # Small delay to increase chance of race conditions
    
    # Create multiple threads updating the state
    threads = []
    for i in range(3):
        t = threading.Thread(target=update_worker, args=(i * 1000, 100, 50))
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Get final snapshot - should not crash
    snapshot = state.get_snapshot()
    print(f"Final downloaded: {snapshot.downloaded}, percentage: {snapshot.percentage}%")
    
    print("✓ Thread safety test passed")
    return True


def test_speed_and_eta_calculation():
    """Test that speed and ETA never go negative."""
    print("Testing speed and ETA calculations...")
    
    state = ProgressState(queue_id=1, total=100000)
    
    # Update with increasing values
    state.update(downloaded=1000, total=100000)
    time.sleep(0.1)  # Small delay
    state.update(downloaded=2000, total=100000)
    
    snapshot = state.get_snapshot()
    
    # Speed should never be negative
    assert snapshot.speed_bps >= 0, f"Speed should not be negative, got {snapshot.speed_bps}"
    
    # Test ETA calculation
    if snapshot.eta_seconds is not None:
        assert snapshot.eta_seconds >= 0, f"ETA should not be negative, got {snapshot.eta_seconds}"
    
    print("✓ Speed and ETA calculation test passed")
    return True


def test_phase_transitions():
    """Test phase transitions."""
    print("Testing phase transitions...")
    
    state = ProgressState(queue_id=1, total=100000)
    
    # Initial phase should be CONNECTING
    snapshot = state.get_snapshot()
    assert snapshot.phase == ProgressPhase.CONNECTING, f"Expected CONNECTING, got {snapshot.phase}"
    
    # After downloading some data, should transition to DOWNLOADING
    state.update(downloaded=1000, total=100000)
    snapshot = state.get_snapshot()
    assert snapshot.phase == ProgressPhase.DOWNLOADING, f"Expected DOWNLOADING, got {snapshot.phase}"
    
    # Manual phase change should work
    state.set_phase(ProgressPhase.FINALIZING)
    snapshot = state.get_snapshot()
    assert snapshot.phase == ProgressPhase.FINALIZING, f"Expected FINALIZING, got {snapshot.phase}"
    
    print("✓ Phase transitions test passed")
    return True


def test_terminal_width_handling():
    """Test terminal width handling."""
    print("Testing terminal width handling...")
    
    from src.application.progress.progress_manager import ProgressManager
    
    # Create a progress manager and test that it handles terminal size changes
    progress = ProgressManager(queue_id=1, total_size=100000)
    
    # This should not crash even if terminal size is not available in some environments
    try:
        # Simulate an update which will trigger rendering
        progress.update(50000, 100000)
        progress.finish()
        print("✓ Terminal width handling test passed")
        return True
    except Exception as e:
        print(f"✗ Terminal width handling test failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("Running State 1 progress hardening tests...\n")
    
    tests = [
        test_snapshot_immutability,
        test_percent_clamping,
        test_value_clamping_in_state,
        test_thread_safety,
        test_speed_and_eta_calculation,
        test_phase_transitions,
        test_terminal_width_handling,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)