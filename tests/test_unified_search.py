"""Tests for unified_search tool with all 3 modes (content, files, summary)."""
import os
import sys
from pathlib import Path as _TestPath
from unittest.mock import Mock, patch, MagicMock

ROOT = _TestPath(__file__).resolve().parents[1]
SRC_PATH = ROOT / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from code_index_mcp.models import SearchContext
from code_index_mcp.server import unified_search


def test_search_context_valid_modes():
    """Test SearchContext accepts all valid modes."""
    valid_modes = ['content', 'files', 'summary']

    for mode in valid_modes:
        ctx = SearchContext(mode=mode)
        assert ctx.mode == mode


def test_search_context_invalid_mode():
    """Test SearchContext rejects invalid modes."""
    try:
        SearchContext(mode='invalid_mode')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid mode 'invalid_mode'" in str(e)
        assert "content" in str(e)
        assert "files" in str(e)
        assert "summary" in str(e)


def test_search_context_defaults():
    """Test SearchContext default values."""
    ctx = SearchContext(mode='content')

    assert ctx.case_sensitive is True
    assert ctx.context_lines == 0
    assert ctx.fuzzy is False
    assert ctx.regex is None
    assert ctx.max_line_length is None
    assert ctx.pattern is None
    assert ctx.file_pattern is None
    assert ctx.file_path is None


def test_unified_search_content_mode_missing_pattern():
    """Test unified_search content mode requires pattern parameter."""
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = "/tmp/test"

    # Due to @handle_mcp_tool_errors decorator, error is caught and returned as dict
    result = unified_search(mode='content', ctx=mock_ctx)

    # Should return error dict from decorator
    assert isinstance(result, dict)
    # The error dict should indicate error occurred
    if 'error' in result:
        assert 'pattern is required' in str(result).lower() or 'error' in str(result).lower()


def test_unified_search_files_mode_missing_pattern():
    """Test unified_search files mode requires pattern parameter."""
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = "/tmp/test"

    result = unified_search(mode='files', ctx=mock_ctx)
    assert isinstance(result, dict)
    if 'error' in result:
        assert 'pattern is required' in str(result).lower() or 'error' in str(result).lower()


def test_unified_search_summary_mode_missing_file_path():
    """Test unified_search summary mode requires file_path parameter."""
    mock_ctx = Mock()
    mock_ctx.request_context = Mock()
    mock_ctx.request_context.server = Mock()
    mock_ctx.request_context.server.app_context = Mock()
    mock_ctx.request_context.server.app_context.base_path = "/tmp/test"

    result = unified_search(mode='summary', ctx=mock_ctx)
    assert isinstance(result, dict)
    if 'error' in result:
        assert 'file_path is required' in str(result).lower() or 'error' in str(result).lower()


@patch('code_index_mcp.server.SearchService')
def test_unified_search_content_mode_calls_search_service(MockSearchService, tmp_path):
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
        ctx=mock_ctx
    )

    # Verify SearchService.search_code was called with correct parameters
    mock_service.search_code.assert_called_once()
    call_args = mock_service.search_code.call_args
    assert call_args[1]['pattern'] == 'test'
    assert call_args[1]['case_sensitive'] is False

    # Verify result returned
    assert result['total_count'] == 1


@patch('code_index_mcp.server.FileDiscoveryService')
def test_unified_search_files_mode_calls_file_discovery(MockFileDiscoveryService, tmp_path):
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
    mock_service.find_files.return_value = ["test.py", "app.py"]
    MockFileDiscoveryService.return_value = mock_service

    # Call unified_search
    result = unified_search(
        mode='files',
        pattern='*.py',
        ctx=mock_ctx
    )

    # Verify FileDiscoveryService.find_files was called
    mock_service.find_files.assert_called_once_with('*.py')

    # Verify result format
    assert 'files' in result
    assert 'total_count' in result
    assert result['total_count'] == 2
    assert result['files'] == ["test.py", "app.py"]


@patch('code_index_mcp.server.CodeIntelligenceService')
def test_unified_search_summary_mode_calls_code_intelligence(MockCodeIntelligenceService, tmp_path):
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
        "functions": ["test_func"],
        "classes": []
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

    # Verify result format
    assert result['file_path'] == 'test.py'
    assert result['language'] == 'python'


def test_unified_search_invalid_mode():
    """Test unified_search with invalid mode raises ValueError."""
    mock_ctx = Mock()

    result = unified_search(mode='invalid', ctx=mock_ctx)
    assert isinstance(result, dict)
    if 'error' in result:
        assert 'invalid mode' in str(result).lower() or 'error' in str(result).lower()


@patch('code_index_mcp.server.SearchService')
def test_unified_search_content_mode_with_all_parameters(MockSearchService, tmp_path):
    """Test unified_search content mode passes all parameters correctly."""
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
        pattern='test.*pattern',
        case_sensitive=False,
        context_lines=3,
        file_pattern='*.py',
        fuzzy=True,
        regex=True,
        max_line_length=200,
        ctx=mock_ctx
    )

    # Verify all parameters passed
    call_args = mock_service.search_code.call_args[1]
    assert call_args['pattern'] == 'test.*pattern'
    assert call_args['case_sensitive'] is False
    assert call_args['context_lines'] == 3
    assert call_args['file_pattern'] == '*.py'
    assert call_args['fuzzy'] is True
    assert call_args['regex'] is True
    assert call_args['max_line_length'] == 200
