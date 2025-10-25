"""
Code indexing utilities for the MCP server.

This module provides simple JSON-based indexing optimized for LLM consumption.
"""

# Import utility functions that are still used
from .qualified_names import (
    generate_qualified_name,
    normalize_file_path
)

# New JSON-based indexing system
from .json_index_builder import JSONIndexBuilder, IndexMetadata
from .layered_index_manager import LayeredIndexManager, get_layered_index_manager
from .models import SymbolInfo, FileInfo

__all__ = [
    'generate_qualified_name',
    'normalize_file_path',
    'JSONIndexBuilder',
    'LayeredIndexManager',
    'get_layered_index_manager',
    'SymbolInfo',
    'FileInfo',
    'IndexMetadata'
]