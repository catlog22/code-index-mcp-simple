"""Tests for SearchContext dataclass validation and behavior."""
import os
import sys
from pathlib import Path as _TestPath

ROOT = _TestPath(__file__).resolve().parents[2]
SRC_PATH = ROOT / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from code_index_mcp.models import SearchContext


def test_search_context_valid_content_mode():
    """Test SearchContext with valid content mode."""
    ctx = SearchContext(mode='content', pattern='test')
    assert ctx.mode == 'content'
    assert ctx.pattern == 'test'


def test_search_context_valid_files_mode():
    """Test SearchContext with valid files mode."""
    ctx = SearchContext(mode='files', pattern='*.py')
    assert ctx.mode == 'files'
    assert ctx.pattern == '*.py'


def test_search_context_valid_summary_mode():
    """Test SearchContext with valid summary mode."""
    ctx = SearchContext(mode='summary', file_path='/path/to/file.py')
    assert ctx.mode == 'summary'
    assert ctx.file_path == '/path/to/file.py'


def test_search_context_invalid_mode():
    """Test SearchContext raises ValueError for invalid mode."""
    try:
        SearchContext(mode='invalid_mode')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid mode 'invalid_mode'" in str(e)
        assert 'content' in str(e)
        assert 'files' in str(e)
        assert 'summary' in str(e)


def test_search_context_default_values():
    """Test SearchContext uses correct default values."""
    ctx = SearchContext(mode='content')

    assert ctx.case_sensitive is True
    assert ctx.context_lines == 0
    assert ctx.fuzzy is False
    assert ctx.regex is None
    assert ctx.max_line_length is None
    assert ctx.pattern is None
    assert ctx.file_pattern is None
    assert ctx.file_path is None


def test_search_context_all_parameters():
    """Test SearchContext with all parameters specified."""
    ctx = SearchContext(
        mode='content',
        pattern='test.*pattern',
        case_sensitive=False,
        context_lines=3,
        file_pattern='*.py',
        fuzzy=True,
        regex=True,
        max_line_length=200,
        file_path='/some/file.py'
    )

    assert ctx.mode == 'content'
    assert ctx.pattern == 'test.*pattern'
    assert ctx.case_sensitive is False
    assert ctx.context_lines == 3
    assert ctx.file_pattern == '*.py'
    assert ctx.fuzzy is True
    assert ctx.regex is True
    assert ctx.max_line_length == 200
    assert ctx.file_path == '/some/file.py'


def test_search_context_empty_pattern():
    """Test SearchContext accepts empty pattern (validation happens in tool layer)."""
    ctx = SearchContext(mode='content', pattern='')
    assert ctx.pattern == ''


def test_search_context_none_pattern():
    """Test SearchContext accepts None pattern (validation happens in tool layer)."""
    ctx = SearchContext(mode='content', pattern=None)
    assert ctx.pattern is None


def test_search_context_boundary_context_lines():
    """Test SearchContext with boundary context_lines values."""
    # Zero context lines (default)
    ctx1 = SearchContext(mode='content', context_lines=0)
    assert ctx1.context_lines == 0

    # Large context lines
    ctx2 = SearchContext(mode='content', context_lines=100)
    assert ctx2.context_lines == 100

    # Negative context lines (allowed, validation in service layer)
    ctx3 = SearchContext(mode='content', context_lines=-1)
    assert ctx3.context_lines == -1


def test_search_context_boundary_max_line_length():
    """Test SearchContext with boundary max_line_length values."""
    # None (unlimited)
    ctx1 = SearchContext(mode='content', max_line_length=None)
    assert ctx1.max_line_length is None

    # Small value
    ctx2 = SearchContext(mode='content', max_line_length=10)
    assert ctx2.max_line_length == 10

    # Large value
    ctx3 = SearchContext(mode='content', max_line_length=100000)
    assert ctx3.max_line_length == 100000
