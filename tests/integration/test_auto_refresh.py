"""Integration tests for automatic index refresh mechanism."""
import os
import sys
import time
from pathlib import Path as _TestPath
from unittest.mock import Mock, patch

ROOT = _TestPath(__file__).resolve().parents[2]
SRC_PATH = ROOT / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from code_index_mcp.indexing.layered_index_manager import LayeredIndexManager


def test_auto_refresh_on_stale_index(tmp_path):
    """Test that index automatically refreshes when source files change."""
    # Create test project
    test_file = tmp_path / "app.py"
    test_file.write_text("def version_1():\n    pass\n")

    # Initialize manager and build index
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build initial index
    index1 = manager.get_global_index(shallow=False, force_rebuild=True)
    assert index1 is not None

    # Get initial metadata
    initial_build_time = index1['_metadata']['build_time']

    # Modify source file (simulating code change)
    time.sleep(0.1)  # Ensure mtime difference
    test_file.write_text("def version_2():\n    pass\n")

    # Mock _is_index_fresh to return False (stale)
    with patch.object(manager, '_is_index_fresh', return_value=False):
        # Get index again - should detect staleness and rebuild
        index2 = manager.get_global_index(shallow=False, force_rebuild=False)

        # Verify rebuild occurred (new build time)
        new_build_time = index2['_metadata']['build_time']
        assert new_build_time > initial_build_time


def test_freshness_check_performance(tmp_path):
    """Test that freshness check is fast even for large projects."""
    # Create test project with multiple files
    for i in range(50):
        (tmp_path / f"file_{i}.py").write_text(f"# File {i}\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build index
    manager.get_global_index(shallow=True, force_rebuild=True)

    # Time freshness check
    start_time = time.time()
    is_fresh = manager._is_index_fresh(manager.global_shallow_path)
    duration = time.time() - start_time

    # Freshness check should be fast (<1 second for 50 files)
    assert duration < 1.0
    assert is_fresh is True


def test_skip_refresh_when_fresh(tmp_path):
    """Test that refresh is skipped when index is already fresh."""
    # Create test project
    (tmp_path / "app.py").write_text("def main():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build index
    index1 = manager.get_global_index(shallow=False, force_rebuild=True)
    build_time_1 = index1['_metadata']['build_time']

    # Wait briefly
    time.sleep(0.1)

    # Get index again without force_rebuild
    index2 = manager.get_global_index(shallow=False, force_rebuild=False)
    build_time_2 = index2['_metadata']['build_time']

    # Build time should be same (cache was used)
    assert build_time_1 == build_time_2


def test_rebuild_on_stale_index(tmp_path):
    """Test that rebuild is triggered when index is stale."""
    # Create test project
    test_file = tmp_path / "module.py"
    test_file.write_text("def func_v1():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build index
    index1 = manager.get_global_index(shallow=False, force_rebuild=True)
    assert index1 is not None

    # Modify file to make index stale
    time.sleep(0.2)
    test_file.write_text("def func_v2():\n    pass\n")

    # Force freshness check to detect change
    is_fresh = manager._is_index_fresh(manager.global_index_path)
    assert is_fresh is False  # Index should be stale

    # Rebuild should be triggered on next access
    index2 = manager.get_global_index(shallow=False, force_rebuild=True)

    # Verify new build occurred
    assert index2['_metadata']['build_time'] > index1['_metadata']['build_time']


def test_mtime_based_freshness_detection(tmp_path):
    """Test that freshness detection uses file modification times."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("def original():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build index
    manager.get_global_index(shallow=True, force_rebuild=True)

    # Get index mtime
    index_mtime = os.path.getmtime(manager.global_shallow_path)

    # Verify index is fresh
    assert manager._is_index_fresh(manager.global_shallow_path) is True

    # Touch file to update mtime (simulate edit)
    time.sleep(0.1)
    test_file.touch()
    new_file_mtime = os.path.getmtime(test_file)

    # File should be newer than index
    assert new_file_mtime > index_mtime

    # Index should now be stale
    assert manager._is_index_fresh(manager.global_shallow_path) is False


def test_max_source_mtime_calculation(tmp_path):
    """Test calculation of maximum source file modification time."""
    # Create files with different mtimes
    file1 = tmp_path / "old.py"
    file2 = tmp_path / "new.py"

    file1.write_text("# old file")
    time.sleep(0.1)
    file2.write_text("# new file")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Calculate max mtime
    max_mtime = manager._get_max_source_mtime(str(tmp_path))

    # Should return mtime of newest file
    file2_mtime = os.path.getmtime(file2)
    assert abs(max_mtime - file2_mtime) < 0.01  # Allow small float difference


def test_freshness_check_with_subdirectories(tmp_path):
    """Test freshness check works with nested directories."""
    # Create nested structure
    subdir = tmp_path / "src" / "utils"
    subdir.mkdir(parents=True)

    (tmp_path / "app.py").write_text("# root file")
    (subdir / "helper.py").write_text("# nested file")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build index
    manager.get_global_index(shallow=True, force_rebuild=True)

    # Verify fresh
    assert manager._is_index_fresh(manager.global_shallow_path) is True

    # Modify nested file
    time.sleep(0.1)
    (subdir / "helper.py").write_text("# modified nested file")

    # Index should be stale
    assert manager._is_index_fresh(manager.global_shallow_path) is False


def test_concurrent_freshness_checks(tmp_path):
    """Test that concurrent freshness checks don't cause issues."""
    import threading

    # Create test project
    (tmp_path / "app.py").write_text("def main():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))
    manager.get_global_index(shallow=True, force_rebuild=True)

    results = []

    def check_freshness():
        is_fresh = manager._is_index_fresh(manager.global_shallow_path)
        results.append(is_fresh)

    # Run concurrent freshness checks
    threads = [threading.Thread(target=check_freshness) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All checks should return True (index is fresh)
    assert all(results)
    assert len(results) == 5


def test_index_rebuild_updates_metadata(tmp_path):
    """Test that index rebuild updates metadata correctly."""
    # Create test file
    (tmp_path / "test.py").write_text("def func():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build initial index
    index1 = manager.get_global_index(shallow=False, force_rebuild=True)
    metadata1 = index1['_metadata']

    # Wait and rebuild
    time.sleep(0.1)
    index2 = manager.get_global_index(shallow=False, force_rebuild=True)
    metadata2 = index2['_metadata']

    # Metadata should be updated
    assert metadata2['build_time'] > metadata1['build_time']
    assert 'max_mtime' in metadata2
    assert 'files_indexed' in metadata2
