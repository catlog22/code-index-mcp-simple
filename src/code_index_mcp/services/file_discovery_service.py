"""
File Discovery Service - Business logic for intelligent file discovery.

This service handles the business logic for finding files using the new
JSON-based indexing system optimized for LLM consumption.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base_service import BaseService
from ..indexing import get_layered_index_manager


@dataclass
class FileDiscoveryResult:
    """Business result for file discovery operations."""
    files: List[str]
    total_count: int
    pattern_used: str
    search_strategy: str
    metadata: Dict[str, Any]


class FileDiscoveryService(BaseService):
    """
    Business service for intelligent file discovery using JSON indexing.

    This service provides fast file discovery using the optimized JSON
    indexing system for efficient LLM-oriented responses.
    """

    def __init__(self, ctx):
        super().__init__(ctx)
        self._index_manager = get_layered_index_manager()

    def find_files(self, pattern: str, max_results: Optional[int] = None) -> List[str]:
        """
        Find files matching the given pattern using JSON indexing.

        Args:
            pattern: Search pattern - can be:
                - Glob pattern: "*.py", "test_*.js", "src/**/*.ts"
                - Simple text: "heat" (auto-converted to "*heat*")
                - Wildcards will be added automatically if pattern doesn't contain glob chars
            max_results: Maximum number of results to return (None for no limit)

        Returns:
            List of file paths matching the pattern

        Raises:
            ValueError: If pattern is invalid or project not set up
        """
        # Business validation
        self._validate_discovery_request(pattern)

        # Auto-refresh: Ensure shallow index is fresh before file discovery
        # Shallow index contains file list which is all we need for pattern matching
        self._ensure_index_fresh(target_path=None, shallow=True)

        # Smart pattern conversion: if pattern doesn't contain glob chars, add wildcards
        glob_chars = ['*', '?', '[', ']']
        has_glob = any(char in pattern for char in glob_chars)

        if not has_glob:
            # Simple text search - wrap with wildcards for substring matching
            search_pattern = f"*{pattern}*"
        else:
            # User provided glob pattern - use as is
            search_pattern = pattern

        # Get files from JSON index
        files = self._index_manager.find_files(search_pattern)

        # Apply max_results limit if specified
        if max_results and len(files) > max_results:
            files = files[:max_results]

        return files

    def _validate_discovery_request(self, pattern: str) -> None:
        """
        Validate the file discovery request according to business rules.

        Args:
            pattern: Pattern to validate

        Raises:
            ValueError: If validation fails
        """
        # Ensure project is set up
        self._require_project_setup()

        # Validate pattern
        if not pattern or not pattern.strip():
            raise ValueError("Search pattern cannot be empty")
