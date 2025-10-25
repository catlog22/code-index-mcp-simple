"""
Code Index MCP Server

This MCP server allows LLMs to index, search, and analyze code from a project directory.
It provides tools for file discovery, content retrieval, and code analysis.

This version uses a service-oriented architecture where MCP decorators delegate
to domain-specific services for business logic.
"""

# Standard library imports
import sys
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Any, List, Optional

# Third-party imports
from mcp.server.fastmcp import FastMCP, Context

# Local imports
from .project_settings import ProjectSettings, migrate_legacy_config
from .models import SearchContext
from .services import (
    SearchService, FileService
)
from .services.file_discovery_service import FileDiscoveryService
from .services.project_management_service import ProjectManagementService
from .services.index_management_service import IndexManagementService
from .services.code_intelligence_service import CodeIntelligenceService
from .utils import (
    handle_mcp_resource_errors, handle_mcp_tool_errors
)

# Setup logging without writing to files
def setup_indexing_performance_logging():
    """Setup logging (stderr only); remove any file-based logging."""

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # stderr for errors only
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    stderr_handler.setLevel(logging.ERROR)

    root_logger.addHandler(stderr_handler)
    root_logger.setLevel(logging.DEBUG)

# Initialize logging (no file handlers)
setup_indexing_performance_logging()

@dataclass
class CodeIndexerContext:
    """Context for the Code Indexer MCP server."""
    base_path: str
    settings: ProjectSettings
    file_count: int = 0

@asynccontextmanager
async def indexer_lifespan(_server: FastMCP) -> AsyncIterator[CodeIndexerContext]:
    """Manage the lifecycle of the Code Indexer MCP server."""
    # Don't set a default path, user must explicitly set project path
    base_path = ""  # Empty string to indicate no path is set

    # Initialize settings manager with skip_load=True to skip loading files
    settings = ProjectSettings(base_path, skip_load=True)

    # Perform configuration migration from legacy config.json to MCP Config
    # This runs before any services are initialized to ensure config is ready
    try:
        if settings.settings_path:
            migrated_config = migrate_legacy_config(settings.settings_path)
            settings.set_mcp_config(migrated_config)

            migration_source = migrated_config.get("_migration", {}).get("source", "unknown")
            if migration_source == "legacy":
                logging.info("Config migrated from legacy config.json")
            elif migration_source == "default":
                logging.info("Using default configuration (no legacy config found)")
            elif migration_source == "partial":
                logging.warning("Partial migration completed, some settings use defaults")
            elif migration_source == "default_fallback":
                logging.warning("Migration failed, using default configuration")
    except Exception as e:
        # Don't block server startup on migration failure
        logging.error(f"Config migration error: {e}, using defaults")
        # settings already has default config initialized

    # Initialize context
    context = CodeIndexerContext(
        base_path=base_path,
        settings=settings
    )

    try:
        # Provide context to the server
        yield context
    finally:
        # Cleanup (no file watcher to stop anymore)
        pass

# Create the MCP server with lifespan manager
mcp = FastMCP("CodeIndexer", lifespan=indexer_lifespan, dependencies=["pathlib"])

# ----- RESOURCES -----

@mcp.resource("config://code-indexer")
@handle_mcp_resource_errors
def get_config() -> str:
    """Get the current configuration of the Code Indexer."""
    ctx = mcp.get_context()
    return ProjectManagementService(ctx).get_project_config()

@mcp.resource("files://{file_path}")
@handle_mcp_resource_errors
def get_file_content(file_path: str) -> str:
    """Get the content of a specific file."""
    ctx = mcp.get_context()
    # Use FileService for simple file reading - this is appropriate for a resource
    return FileService(ctx).get_file_content(file_path)

# Removed: structure://project resource - not necessary for most workflows
# Removed: settings://stats resource - this information is available via get_settings_info() tool
# and is more of a debugging/technical detail rather than context AI needs

# ----- TOOLS -----

# Removed set_project_path - functionality merged into unified_search
# Users can now set project path directly in unified_search with the project_path parameter

@mcp.tool()
@handle_mcp_tool_errors(return_type='dict')
def unified_search(
    mode: str,
    project_path: str,
    ctx: Context,
    query: Optional[str] = None,
    case_sensitive: bool = True,
    context_lines: int = 0,
    file_pattern: Optional[str] = None,
    fuzzy: bool = False,
    regex: Optional[bool] = None,
    max_line_length: Optional[int] = None,
    file_path: Optional[str] = None,
    auto_index: bool = True
) -> Dict[str, Any]:
    """
    Unified search interface supporting multiple search modes.

    This is the ONE TOOL you need! It can set project path, build indexes,
    and perform searches - all in a single call for maximum convenience.

    Args:
        mode: Search mode - one of:
            - 'content': Search code content (requires: query)
            - 'files': Find files by name (requires: query)
            - 'summary': Analyze file structure (requires: file_path)
        project_path: **REQUIRED** - Absolute path to the project directory.
            Automatically initializes the project and builds indexes before searching.
            This means you can do everything in ONE call!
        query: Search query (REQUIRED for 'content' and 'files' modes)
            - For 'content' mode: Text or regex pattern to search in code
            - For 'files' mode: File name pattern - supports:
                * Simple text: "heat" (finds files containing "heat" in name)
                * Glob patterns: "*.py" (all Python files), "test_*" (files starting with test_)
                * Auto-conversion: simple text without wildcards gets wrapped as "*text*"
        case_sensitive: Whether search is case-sensitive (default: True)
        context_lines: Number of context lines to show (default: 0)
        file_pattern: Glob pattern to filter files (e.g., "*.py")
        fuzzy: Enable fuzzy/partial matching (default: False)
        regex: Enable regex pattern matching (default: None for auto-detect)
        max_line_length: Maximum length of lines in results (default: None)
        file_path: Relative path to file for analysis (REQUIRED for 'summary' mode)
            Example: "src/main.py" or "lib/utils.js"
        auto_index: Auto-build shallow index when project_path is provided (default: True)

    Returns:
        Search results in mode-appropriate format, with optional setup status

    Raises:
        ValueError: If mode is invalid or required parameters are missing

    Examples:
        # Content search - find code containing text
        unified_search(
            mode='content',
            project_path='D:\\\\my-project',
            query='fluid'
        )

        # Files search - find files by name (auto-converts to glob)
        unified_search(
            mode='files',
            project_path='D:\\\\my-project',
            query='heat'  # Finds all files with "heat" in filename (auto: *heat*)
        )

        # Files search - explicit glob pattern
        unified_search(
            mode='files',
            project_path='D:\\\\my-project',
            query='*.py'  # Finds all Python files
        )

        # Summary mode - analyze a specific file
        unified_search(
            mode='summary',
            project_path='D:\\\\my-project',
            file_path='src/main.py'
        )
    """
    # Initialize project (project_path is now required)
    try:
        # Initialize project
        result = ProjectManagementService(ctx).initialize_project(project_path)
        setup_status = {"project_initialization": result}

        # Auto-build shallow index if requested
        if auto_index:
            try:
                IndexManagementService(ctx).rebuild_index()
                setup_status["shallow_index"] = "✅ Auto-indexed files"
            except Exception as e:
                setup_status["shallow_index"] = f"⚠️ Warning: {e}"

        # Smart deep index building: only for summary mode
        if mode == 'summary':
            try:
                IndexManagementService(ctx).rebuild_deep_index()
                setup_status["deep_index"] = "✅ Deep index built (required for summary mode)"
            except Exception as e:
                setup_status["deep_index"] = f"⚠️ Warning: {e}"
        else:
            # Skip deep index for content/files modes (not needed)
            setup_status["deep_index"] = f"⏭️ Skipped (not needed for '{mode}' mode)"
    except Exception as e:
        raise ValueError(f"Project initialization failed: {e}") from e

    # Create SearchContext from parameters
    try:
        search_ctx = SearchContext(
            mode=mode,
            pattern=query,  # Use query instead of pattern
            case_sensitive=case_sensitive,
            context_lines=context_lines,
            file_pattern=file_pattern,
            fuzzy=fuzzy,
            regex=regex,
            max_line_length=max_line_length,
            file_path=file_path
        )
    except ValueError as e:
        raise ValueError(f"Invalid search parameters: {e}") from e

    # Validate mode-specific required parameters and execute search
    search_results = None
    if mode == 'content':
        if not query:
            raise ValueError("query is required for content mode")
        search_results = SearchService(ctx).search_code(
            pattern=search_ctx.pattern,
            case_sensitive=search_ctx.case_sensitive,
            context_lines=search_ctx.context_lines,
            file_pattern=search_ctx.file_pattern,
            fuzzy=search_ctx.fuzzy,
            regex=search_ctx.regex,
            max_line_length=search_ctx.max_line_length
        )
    elif mode == 'files':
        if not query:
            raise ValueError("query is required for files mode")
        files = FileDiscoveryService(ctx).find_files(search_ctx.pattern)
        search_results = {"files": files, "total_count": len(files)}
    elif mode == 'summary':
        if not file_path:
            raise ValueError(
                "file_path is required for summary mode. "
                "Please provide the relative path to a file (e.g., 'src/main.py'). "
                "Use mode='files' with query='*.py' to discover available files first."
            )
        search_results = CodeIntelligenceService(ctx).analyze_file(search_ctx.file_path)
    else:
        # This should never happen due to SearchContext validation, but defensive
        raise ValueError(f"Unsupported mode: {mode}")

    # Always return combined setup status with search results
    return {
        "setup": setup_status,
        "search": search_results
    }


# Removed refresh_index and build_deep_index - functionality merged into unified_search
# Users can control indexing behavior with auto_index parameter in unified_search
# Deep index is automatically built only for summary mode

# API Simplification Summary:
# - Removed 10 tools total, keeping only unified_search
# - unified_search now handles: project setup, indexing, and all search modes
# - Single-tool workflow: unified_search(mode, query, project_path)
#
# Previously removed tools:
# - set_project_path (merged into unified_search via project_path parameter)
# - refresh_index (merged into unified_search via auto_index parameter)
# - build_deep_index (automatic for summary mode, removed as separate tool)
# - get_settings_info (debugging tool)
# - create_temp_directory (lifecycle managed)
# - check_temp_directory (debugging tool)
# - clear_settings (destructive operation)
# - refresh_search_tools (auto-detected)
# - get_file_watcher_status (observability)
# - configure_file_watcher (default config sufficient)
#
# Simplified workflow: ONE TOOL for everything!
# unified_search(mode='content', query='search', project_path='D:\\project')

# ----- PROMPTS -----
# Removed: analyze_code, code_search, set_project prompts

def main():
    """Main function to run the MCP server."""
    mcp.run()

if __name__ == '__main__':
    main()
