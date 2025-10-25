"""Tests for BaseService auto-refresh mechanism and common functionality."""
import os
import sys
import time
from pathlib import Path as _TestPath
from unittest.mock import Mock, patch, MagicMock

ROOT = _TestPath(__file__).resolve().parents[2]
SRC_PATH = ROOT / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from code_index_mcp.services.base_service import BaseService


class MockService(BaseService):
    """Mock service for testing BaseService functionality."""
    pass


def test_base_service_initialization():
    """Test BaseService initializes with Context."""
    mock_ctx = Mock()
    service = MockService(mock_ctx)

    assert service.ctx == mock_ctx
    assert service.helper is not None


def test_base_service_mtime_cache_shared():
    """Test BaseService mtime cache is shared across instances."""
    mock_ctx = Mock()
    service1 = MockService(mock_ctx)
    service2 = MockService(mock_ctx)

    # Both services should share the same class-level cache
    assert service1._mtime_cache is service2._mtime_cache


@patch('code_index_mcp.indexing.get_layered_index_manager')
def test_ensure_index_fresh_missing_index_triggers_rebuild(mock_get_manager, tmp_path):
    """Test _ensure_index_fresh triggers rebuild when index is missing."""
    # Setup mocks
    mock_ctx = Mock()

    mock_manager = Mock()
    mock_manager.project_path = str(tmp_path)
    mock_manager.global_index_path = str(tmp_path / 'nonexistent.json')
    mock_manager.global_shallow_path = str(tmp_path / 'nonexistent.shallow.json')
    mock_manager.get_global_index.return_value = {}
    mock_get_manager.return_value = mock_manager

    service = MockService(mock_ctx)

    # Mock base_path property
    type(service.helper).base_path = property(lambda self: str(tmp_path))

    # Call _ensure_index_fresh
    result = service._ensure_index_fresh(target_path=None, shallow=False)

    # Should trigger rebuild via get_global_index
    assert mock_manager.get_global_index.called
    assert result is True


@patch('code_index_mcp.indexing.get_layered_index_manager')
def test_ensure_index_fresh_stale_index_triggers_rebuild(mock_get_manager, tmp_path):
    """Test _ensure_index_fresh triggers rebuild when index is stale."""
    # Create index file with old mtime
    index_file = tmp_path / 'index.json'
    index_file.write_text('{}')
    old_time = time.time() - 1000
    os.utime(index_file, (old_time, old_time))

    # Setup mocks
    mock_ctx = Mock()

    mock_manager = Mock()
    mock_manager.project_path = str(tmp_path)
    mock_manager.global_index_path = str(index_file)
    mock_manager.global_shallow_path = str(tmp_path / 'index.shallow.json')
    mock_manager._get_max_source_mtime.return_value = time.time()  # Current time (newer)
    mock_manager.get_global_index.return_value = {}
    mock_get_manager.return_value = mock_manager

    service = MockService(mock_ctx)

    # Mock base_path property
    type(service.helper).base_path = property(lambda self: str(tmp_path))

    # Call _ensure_index_fresh
    result = service._ensure_index_fresh(target_path=None, shallow=False)

    # Should trigger rebuild
    assert mock_manager.get_global_index.called
    assert result is True


@patch('code_index_mcp.indexing.get_layered_index_manager')
def test_ensure_index_fresh_fresh_index_no_rebuild(mock_get_manager, tmp_path):
    """Test _ensure_index_fresh skips rebuild when index is fresh."""
    # Create index file with current mtime
    index_file = tmp_path / 'index.json'
    index_file.write_text('{}')
    current_time = time.time()
    os.utime(index_file, (current_time, current_time))

    # Setup mocks
    mock_ctx = Mock()

    mock_manager = Mock()
    mock_manager.project_path = str(tmp_path)
    mock_manager.global_index_path = str(index_file)
    mock_manager.global_shallow_path = str(tmp_path / 'index.shallow.json')
    mock_manager._get_max_source_mtime.return_value = current_time - 100  # Older than index
    mock_get_manager.return_value = mock_manager

    service = MockService(mock_ctx)

    # Mock base_path property
    type(service.helper).base_path = property(lambda self: str(tmp_path))

    # Call _ensure_index_fresh
    result = service._ensure_index_fresh(target_path=None, shallow=False)

    # Should NOT trigger rebuild
    assert not mock_manager.get_global_index.called
    assert not mock_manager.refresh_index.called
    assert result is True


def test_get_cached_max_mtime_caches_results(tmp_path):
    """Test _get_cached_max_mtime caches mtime results."""
    mock_ctx = Mock()
    service = MockService(mock_ctx)

    test_path = str(tmp_path)
    test_mtime = 123456.789

    # Clear cache
    BaseService._mtime_cache.clear()

    with patch('code_index_mcp.indexing.get_layered_index_manager') as mock_get_manager:
        mock_manager = Mock()
        mock_manager._get_max_source_mtime.return_value = test_mtime
        mock_get_manager.return_value = mock_manager

        # First call should query manager
        result1 = service._get_cached_max_mtime(test_path)
        assert result1 == test_mtime
        assert mock_manager._get_max_source_mtime.call_count == 1

        # Second call within TTL should use cache
        result2 = service._get_cached_max_mtime(test_path)
        assert result2 == test_mtime
        assert mock_manager._get_max_source_mtime.call_count == 1  # Not called again

        # Cache entry should exist
        assert test_path in BaseService._mtime_cache


def test_get_cached_max_mtime_expires_after_ttl(tmp_path):
    """Test _get_cached_max_mtime cache expires after TTL."""
    mock_ctx = Mock()
    service = MockService(mock_ctx)

    test_path = str(tmp_path)
    test_mtime = 123456.789

    # Clear cache and set low TTL
    BaseService._mtime_cache.clear()
    original_ttl = BaseService._mtime_cache_ttl
    BaseService._mtime_cache_ttl = 0.1  # 100ms TTL

    try:
        with patch('code_index_mcp.indexing.get_layered_index_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager._get_max_source_mtime.return_value = test_mtime
            mock_get_manager.return_value = mock_manager

            # First call
            result1 = service._get_cached_max_mtime(test_path)
            assert result1 == test_mtime
            assert mock_manager._get_max_source_mtime.call_count == 1

            # Wait for TTL expiration
            time.sleep(0.2)

            # Second call should query manager again
            result2 = service._get_cached_max_mtime(test_path)
            assert result2 == test_mtime
            assert mock_manager._get_max_source_mtime.call_count == 2  # Called again

    finally:
        # Restore original TTL
        BaseService._mtime_cache_ttl = original_ttl
