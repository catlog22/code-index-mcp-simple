"""
SearchContext dataclass for unified search parameter handling.

This module provides a unified data structure for encapsulating all search
parameters across different search modes (content, files, summary).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchContext:
    """
    Encapsulates all search parameters for unified search operations.

    This dataclass provides a single, consistent interface for passing search
    parameters to different search modes and services.

    Attributes:
        mode: Search mode - one of 'content', 'files', or 'summary'
        pattern: Search pattern (required for content/files modes)
        case_sensitive: Whether search is case-sensitive (default: True)
        context_lines: Number of context lines to show (default: 0)
        file_pattern: Glob pattern to filter files (e.g., "*.py")
        fuzzy: Enable fuzzy/partial matching (default: False)
        regex: Enable regex pattern matching (default: None for auto-detect)
        max_line_length: Maximum length of lines in results (default: None)
        file_path: File path for summary mode (required for summary mode)
    """

    mode: str
    pattern: Optional[str] = None
    case_sensitive: bool = True
    context_lines: int = 0
    file_pattern: Optional[str] = None
    fuzzy: bool = False
    regex: Optional[bool] = None
    max_line_length: Optional[int] = None
    file_path: Optional[str] = None

    def __post_init__(self):
        """Validate mode parameter after initialization."""
        valid_modes = {'content', 'files', 'summary'}
        if self.mode not in valid_modes:
            raise ValueError(
                f"Invalid mode '{self.mode}'. Must be one of: {', '.join(sorted(valid_modes))}"
            )
