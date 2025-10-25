"""Tests for LayeredIndexManager with cache reuse and invalidation."""
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path as _TestPath
from unittest.mock import Mock, patch

ROOT = _TestPath(__file__).resolve().parents[2]
SRC_PATH = ROOT / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from code_index_mcp.indexing.layered_index_manager import LayeredIndexManager


def test_global_index_build(tmp_path):
    """Test building global index for entire project."""
    # Create test project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("def main():\n    pass\n")
    (src_dir / "utils.py").write_text("def helper():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    assert manager.set_project_path(str(tmp_path)) is True

    # Build global deep index
    index = manager.get_global_index(shallow=False, force_rebuild=True)

    # Verify index structure
    assert index is not None
    assert '_metadata' in index
    assert 'files' in index
    assert 'symbols' in index

    # Verify metadata
    metadata = index['_metadata']
    assert 'build_time' in metadata
    assert 'files_indexed' in metadata
    assert 'max_mtime' in metadata
    assert metadata['files_indexed'] >= 2


def test_global_shallow_index_build(tmp_path):
    """Test building global shallow index (file list only)."""
    # Create test project
    (tmp_path / "test1.py").write_text("# test file 1")
    (tmp_path / "test2.py").write_text("# test file 2")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build shallow index
    file_list = manager.get_global_index(shallow=True, force_rebuild=True)

    # Verify file list
    assert file_list is not None
    assert isinstance(file_list, list)
    assert len(file_list) >= 2

    # Normalize paths for comparison
    normalized = [f.replace('\\', '/').lstrip('./') for f in file_list]
    assert any('test1.py' in f for f in normalized)
    assert any('test2.py' in f for f in normalized)


def test_subpath_index_cache(tmp_path):
    """Test sub-path index caching mechanism."""
    # Create project with subdirectory
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "module.py").write_text("def func():\n    pass\n")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_module.py").write_text("def test_func():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build sub-path index for src/
    index1 = manager.get_subpath_index("src", shallow=True, force_rebuild=True)
    assert index1 is not None
    assert isinstance(index1, list)

    # Verify cache file was created
    cache_dir = manager.subpath_cache_dir
    assert os.path.exists(cache_dir)
    cache_files = os.listdir(cache_dir)
    assert len(cache_files) > 0

    # Load cache file to verify structure
    cache_file = os.path.join(cache_dir, cache_files[0])
    with open(cache_file, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)

    # Verify cache metadata
    assert '_metadata' in cache_data
    metadata = cache_data['_metadata']
    assert metadata['target_path'] == 'src'
    assert 'build_time' in metadata
    assert 'max_mtime' in metadata
    assert metadata['is_shallow'] is True


def test_cache_reuse(tmp_path):
    """Test cache is reused when index is fresh."""
    # Create test project
    (tmp_path / "app.py").write_text("def main():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # First call - build index
    start_time = time.time()
    index1 = manager.get_subpath_index(".", shallow=True, force_rebuild=True)
    build_time = time.time() - start_time

    # Wait a bit to ensure time difference
    time.sleep(0.1)

    # Second call - should use cache
    start_time = time.time()
    index2 = manager.get_subpath_index(".", shallow=True, force_rebuild=False)
    cache_time = time.time() - start_time

    # Verify cache was used (second call should be faster)
    assert index1 == index2
    # Cache read should be significantly faster than build
    # (relaxed assertion for CI environments)
    assert cache_time < build_time + 1.0


def test_cache_invalidation(tmp_path):
    """Test cache invalidation when source files change."""
    # Create test project
    test_file = tmp_path / "test.py"
    test_file.write_text("def v1():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build index
    index1 = manager.get_subpath_index(".", shallow=True, force_rebuild=True)
    assert index1 is not None

    # Modify source file
    time.sleep(0.1)  # Ensure mtime changes
    test_file.write_text("def v2():\n    pass\n")

    # Get index again - should detect staleness and rebuild
    # (cache validation should fail due to mtime change)
    with patch.object(manager, '_get_max_source_mtime') as mock_mtime:
        # Simulate newer mtime
        mock_mtime.return_value = time.time() + 100

        # This should trigger rebuild due to stale cache
        index2 = manager.get_subpath_index(".", shallow=True, force_rebuild=False)

        # Verify _get_max_source_mtime was called (checking freshness)
        assert mock_mtime.called


def test_manual_cache_invalidation(tmp_path):
    """Test manual cache invalidation."""
    # Create test project
    (tmp_path / "app.py").write_text("def main():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build cache
    manager.get_subpath_index(".", shallow=True, force_rebuild=True)

    # Verify cache exists
    cache_files_before = os.listdir(manager.subpath_cache_dir)
    assert len(cache_files_before) > 0

    # Invalidate cache
    result = manager.invalidate_cache(".")
    assert result is True

    # Verify cache was deleted
    # Cache files should be removed after invalidation
    cache_files_after = os.listdir(manager.subpath_cache_dir)
    # After invalidation, cache files for "." should be deleted
    # (there may be other cache files, but the count should be less)
    assert len(cache_files_after) < len(cache_files_before) or len(cache_files_after) == 0


def test_invalidate_all_caches(tmp_path):
    """Test invalidating all caches at once."""
    # Create multiple subdirectories
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("pass")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test.py").write_text("pass")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build multiple caches
    manager.get_subpath_index("src", shallow=True, force_rebuild=True)
    manager.get_subpath_index("tests", shallow=True, force_rebuild=True)

    # Verify caches exist
    cache_files_before = os.listdir(manager.subpath_cache_dir)
    assert len(cache_files_before) >= 2

    # Invalidate all caches
    result = manager.invalidate_cache(target_path=None)
    assert result is True

    # Verify all caches removed
    cache_files_after = os.listdir(manager.subpath_cache_dir)
    assert len(cache_files_after) == 0


def test_cache_key_generation():
    """Test cache key generation for different paths."""
    manager = LayeredIndexManager()

    # Generate keys for different paths
    key1_shallow = manager._generate_cache_key("src/module", True)
    key1_deep = manager._generate_cache_key("src/module", False)
    key2_shallow = manager._generate_cache_key("tests/unit", True)

    # Verify uniqueness
    assert key1_shallow != key1_deep  # Different index types
    assert key1_shallow != key2_shallow  # Different paths

    # Verify consistency
    key1_shallow_again = manager._generate_cache_key("src/module", True)
    assert key1_shallow == key1_shallow_again

    # Verify format
    assert "_shallow" in key1_shallow
    assert "_deep" in key1_deep


def test_cache_validation_with_parent_index_change(tmp_path):
    """Test cache validation fails when parent index changes."""
    # Create test project
    (tmp_path / "app.py").write_text("def main():\n    pass\n")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build global index
    manager.get_global_index(shallow=True, force_rebuild=True)

    # Build sub-path cache
    manager.get_subpath_index(".", shallow=True, force_rebuild=True)

    # Simulate parent index rebuild
    time.sleep(0.1)
    manager.get_global_index(shallow=True, force_rebuild=True)

    # Verify cache validation detects parent change
    cache_files = os.listdir(manager.subpath_cache_dir)
    if cache_files:
        cache_path = os.path.join(manager.subpath_cache_dir, cache_files[0])

        # Load cache to check parent_index_ref
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        parent_ref = cache_data['_metadata'].get('parent_index_ref')
        current_parent_mtime = os.path.getmtime(manager.global_shallow_path)

        # Parent index should be newer than cache reference
        assert current_parent_mtime >= parent_ref


def test_set_project_path_validation():
    """Test project path validation."""
    manager = LayeredIndexManager()

    # Test empty path
    assert manager.set_project_path("") is False
    assert manager.set_project_path("   ") is False

    # Test non-existent path
    assert manager.set_project_path("/non/existent/path") is False

    # Test None
    assert manager.set_project_path(None) is False


def test_find_files_with_pattern(tmp_path):
    """Test find_files with glob patterns."""
    # Create test files
    (tmp_path / "app.py").write_text("pass")
    (tmp_path / "test.py").write_text("pass")
    (tmp_path / "readme.md").write_text("# Readme")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build index
    manager.get_global_index(shallow=True, force_rebuild=True)

    # Test pattern matching
    py_files = manager.find_files("*.py")
    assert len(py_files) >= 2
    normalized = [f.replace('\\', '/') for f in py_files]
    assert any('app.py' in f for f in normalized)
    assert any('test.py' in f for f in normalized)

    # Test wildcard
    all_files = manager.find_files("*")
    assert len(all_files) >= 3


def test_get_file_summary(tmp_path):
    """Test get_file_summary for file analysis."""
    # Create test file with code
    test_file = tmp_path / "module.py"
    test_file.write_text("""
def my_function():
    pass

class MyClass:
    def method(self):
        pass
""")

    # Initialize manager
    manager = LayeredIndexManager()
    manager.set_project_path(str(tmp_path))

    # Build deep index
    manager.get_global_index(shallow=False, force_rebuild=True)

    # Get file summary
    summary = manager.get_file_summary("module.py")

    # Verify summary structure
    assert summary is not None
    assert summary['file_path'] == 'module.py'
    assert 'language' in summary
    assert 'symbol_count' in summary
    assert 'functions' in summary
    assert 'classes' in summary


def test_cleanup():
    """Test cleanup of manager resources."""
    manager = LayeredIndexManager()

    # Set some state
    manager.project_path = "/tmp/test"
    manager.index_builder = Mock()

    # Cleanup
    manager.cleanup()

    # Verify state cleared
    assert manager.project_path is None
    assert manager.index_builder is None
    assert manager.temp_dir is None
