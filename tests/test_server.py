"""Tests for unified_search MCP tool integration."""
import os
import sys
from pathlib import Path as _TestPath
from unittest.mock import Mock, patch

ROOT = _TestPath(__file__).resolve().parents[1]
SRC_PATH = ROOT / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from code_index_mcp.server import unified_search
from code_index_mcp.models import SearchContext


def test_unified_search_content_mode_missing_pattern():
    """Test unified_search content mode raises error when pattern is missing."""
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = "/tmp/test"

    result = unified_search(mode='content', ctx=mock_ctx)

    # Error caught by decorator, returned as dict
    assert isinstance(result, dict)
    if 'error' in result:
        assert 'pattern' in str(result).lower() or 'error' in str(result).lower()


def test_unified_search_files_mode_missing_pattern():
    """Test unified_search files mode raises error when pattern is missing."""
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = "/tmp/test"

    result = unified_search(mode='files', ctx=mock_ctx)

    assert isinstance(result, dict)
    if 'error' in result:
        assert 'pattern' in str(result).lower() or 'error' in str(result).lower()


def test_unified_search_summary_mode_missing_file_path():
    """Test unified_search summary mode raises error when file_path is missing."""
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = "/tmp/test"

    result = unified_search(mode='summary', ctx=mock_ctx)

    assert isinstance(result, dict)
    if 'error' in result:
        assert 'file_path' in str(result).lower() or 'error' in str(result).lower()


def test_unified_search_invalid_mode():
    """Test unified_search with invalid mode raises ValueError."""
    mock_ctx = Mock()

    result = unified_search(mode='invalid_mode', ctx=mock_ctx)

    assert isinstance(result, dict)
    if 'error' in result:
        assert 'invalid' in str(result).lower() or 'error' in str(result).lower()


@patch('code_index_mcp.server.SearchService')
def test_unified_search_content_mode_delegates_to_search_service(MockSearchService, tmp_path):
    """Test unified_search content mode delegates to SearchService."""
    # Setup mock context
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = str(tmp_path)
    mock_ctx.request_context.server.app_context.settings = Mock()

    # Setup mock search service
    mock_service = Mock()
    mock_service.search_code.return_value = {
        "results": [{"file": "test.py", "line": 1, "content": "test"}],
        "total_count": 1
    }
    MockSearchService.return_value = mock_service

    # Call unified_search
    result = unified_search(
        mode='content',
        pattern='test',
        case_sensitive=False,
        context_lines=3,
        ctx=mock_ctx
    )

    # Verify SearchService.search_code was called
    mock_service.search_code.assert_called_once()
    call_kwargs = mock_service.search_code.call_args[1]
    assert call_kwargs['pattern'] == 'test'
    assert call_kwargs['case_sensitive'] is False
    assert call_kwargs['context_lines'] == 3

    # Verify result
    assert result['total_count'] == 1
    assert len(result['results']) == 1


@patch('code_index_mcp.server.FileDiscoveryService')
def test_unified_search_files_mode_delegates_to_file_discovery(MockFileDiscoveryService, tmp_path):
    """Test unified_search files mode delegates to FileDiscoveryService."""
    # Setup mock context
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = str(tmp_path)
    mock_ctx.request_context.server.app_context.settings = Mock()

    # Setup mock file discovery service
    mock_service = Mock()
    mock_service.find_files.return_value = ["test.py", "app.py", "utils.py"]
    MockFileDiscoveryService.return_value = mock_service

    # Call unified_search
    result = unified_search(
        mode='files',
        pattern='*.py',
        ctx=mock_ctx
    )

    # Verify FileDiscoveryService.find_files was called
    mock_service.find_files.assert_called_once_with('*.py')

    # Verify result structure
    assert 'files' in result
    assert 'total_count' in result
    assert result['total_count'] == 3
    assert result['files'] == ["test.py", "app.py", "utils.py"]


@patch('code_index_mcp.server.CodeIntelligenceService')
def test_unified_search_summary_mode_delegates_to_code_intelligence(MockCodeIntelligenceService, tmp_path):
    """Test unified_search summary mode delegates to CodeIntelligenceService."""
    # Setup mock context
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = str(tmp_path)
    mock_ctx.request_context.server.app_context.settings = Mock()

    # Setup mock code intelligence service
    mock_service = Mock()
    mock_service.analyze_file.return_value = {
        "file_path": "test.py",
        "language": "python",
        "functions": ["main", "helper"],
        "classes": ["TestClass"]
    }
    MockCodeIntelligenceService.return_value = mock_service

    # Call unified_search
    result = unified_search(
        mode='summary',
        file_path='test.py',
        ctx=mock_ctx
    )

    # Verify CodeIntelligenceService.analyze_file was called
    mock_service.analyze_file.assert_called_once_with('test.py')

    # Verify result structure
    assert result['file_path'] == 'test.py'
    assert result['language'] == 'python'
    assert len(result['functions']) == 2
    assert len(result['classes']) == 1


@patch('code_index_mcp.server.SearchService')
def test_unified_search_content_mode_all_parameters(MockSearchService, tmp_path):
    """Test unified_search passes all content mode parameters correctly."""
    # Setup mock context
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = str(tmp_path)
    mock_ctx.request_context.server.app_context.settings = Mock()

    # Setup mock search service
    mock_service = Mock()
    mock_service.search_code.return_value = {"results": [], "total_count": 0}
    MockSearchService.return_value = mock_service

    # Call with all parameters
    unified_search(
        mode='content',
        pattern='test.*regex',
        case_sensitive=False,
        context_lines=5,
        file_pattern='*.py',
        fuzzy=True,
        regex=True,
        max_line_length=150,
        ctx=mock_ctx
    )

    # Verify all parameters passed correctly
    call_kwargs = mock_service.search_code.call_args[1]
    assert call_kwargs['pattern'] == 'test.*regex'
    assert call_kwargs['case_sensitive'] is False
    assert call_kwargs['context_lines'] == 5
    assert call_kwargs['file_pattern'] == '*.py'
    assert call_kwargs['fuzzy'] is True
    assert call_kwargs['regex'] is True
    assert call_kwargs['max_line_length'] == 150


@patch('code_index_mcp.server.FileDiscoveryService')
def test_unified_search_files_mode_empty_results(MockFileDiscoveryService, tmp_path):
    """Test unified_search files mode with empty results."""
    # Setup mock context
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = str(tmp_path)
    mock_ctx.request_context.server.app_context.settings = Mock()

    # Setup mock with empty results
    mock_service = Mock()
    mock_service.find_files.return_value = []
    MockFileDiscoveryService.return_value = mock_service

    # Call unified_search
    result = unified_search(
        mode='files',
        pattern='nonexistent*.xyz',
        ctx=mock_ctx
    )

    # Verify empty results handled correctly
    assert result['total_count'] == 0
    assert result['files'] == []
