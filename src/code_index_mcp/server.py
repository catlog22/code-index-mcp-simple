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
from typing import AsyncIterator, Dict, Any, List

# Third-party imports
from mcp.server.fastmcp import FastMCP, Context

# Local imports
from .project_settings import ProjectSettings, migrate_legacy_config
from .models import SearchContext
from .services import (
    SearchService, FileService, FileWatcherService
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
    file_watcher_service: FileWatcherService = None

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

    # Initialize context - file watcher will be initialized later when project path is set
    context = CodeIndexerContext(
        base_path=base_path,
        settings=settings,
        file_watcher_service=None
    )

    try:
        # Provide context to the server
        yield context
    finally:
        # Stop file watcher if it was started
        if context.file_watcher_service:
            context.file_watcher_service.stop_monitoring()

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

@mcp.tool()
@handle_mcp_tool_errors(return_type='str')
def set_project_path(
    path: str,
    ctx: Context,
    auto_index: bool = True,
    build_deep: bool = True
) -> str:
    """
    Set the base project path and automatically build indexes.

    This is the primary setup command that prepares your project for searching.
    By default, it builds both shallow and deep indexes, making unified_search
    immediately available for all modes (content, files, summary).

    Args:
        path: Absolute path to the project directory
        auto_index: Auto-build shallow index for file discovery (default: True)
        build_deep: Auto-build deep index for code analysis (default: True)

    Returns:
        Status message with indexing information

    Example:
        # Basic usage (recommended) - builds everything automatically
        set_project_path("D:\\my-project")

        # Large project - skip deep index to save time
        set_project_path("D:\\large-project", build_deep=False)

        # Manual control - no auto-indexing
        set_project_path("D:\\project", auto_index=False, build_deep=False)
    """
    # Initialize project
    result = ProjectManagementService(ctx).initialize_project(path)

    # Auto-build shallow index if requested
    if auto_index:
        try:
            IndexManagementService(ctx).refresh_index()
            result += "\n✅ Auto-indexed files (ready for content/files search)"
        except Exception as e:
            result += f"\n⚠️ Warning: Shallow index failed: {e}"

    # Auto-build deep index if requested
    if build_deep:
        try:
            IndexManagementService(ctx).rebuild_deep_index()
            result += "\n✅ Deep index built (ready for summary mode)"
        except Exception as e:
            result += f"\n⚠️ Warning: Deep index failed: {e}"
            result += "\n💡 You can manually run build_deep_index() later"

    if not auto_index and not build_deep:
        result += "\n💡 Remember to run refresh_index() and build_deep_index() before searching"

    return result

@mcp.tool()
@handle_mcp_tool_errors(return_type='dict')
def unified_search(
    mode: str,
    ctx: Context,
    pattern: str = None,
    case_sensitive: bool = True,
    context_lines: int = 0,
    file_pattern: str = None,
    fuzzy: bool = False,
    regex: bool = None,
    max_line_length: int = None,
    file_path: str = None
) -> Dict[str, Any]:
    """
    Unified search interface supporting multiple search modes.

    This tool provides a single entry point for all search operations,
    routing to the appropriate service based on the mode parameter.

    Args:
        mode: Search mode - one of:
            - 'content': Search code content with regex/fuzzy matching
            - 'files': Find files by pattern
            - 'summary': Get file structure analysis
        pattern: Search pattern (required for content/files modes)
        case_sensitive: Whether search is case-sensitive (default: True)
        context_lines: Number of context lines to show (default: 0)
        file_pattern: Glob pattern to filter files (e.g., "*.py")
        fuzzy: Enable fuzzy/partial matching (default: False)
        regex: Enable regex pattern matching (default: None for auto-detect)
        max_line_length: Maximum length of lines in results (default: None)
        file_path: File path for summary mode (required for summary mode)

    Returns:
        Search results in mode-appropriate format

    Raises:
        ValueError: If mode is invalid or required parameters are missing
    """
    # Create SearchContext from parameters
    try:
        search_ctx = SearchContext(
            mode=mode,
            pattern=pattern,
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

    # Validate mode-specific required parameters
    if mode == 'content':
        if not pattern:
            raise ValueError("pattern is required for content mode")
        return SearchService(ctx).search_code(
            pattern=search_ctx.pattern,
            case_sensitive=search_ctx.case_sensitive,
            context_lines=search_ctx.context_lines,
            file_pattern=search_ctx.file_pattern,
            fuzzy=search_ctx.fuzzy,
            regex=search_ctx.regex,
            max_line_length=search_ctx.max_line_length
        )
    elif mode == 'files':
        if not pattern:
            raise ValueError("pattern is required for files mode")
        files = FileDiscoveryService(ctx).find_files(search_ctx.pattern)
        return {"files": files, "total_count": len(files)}
    elif mode == 'summary':
        if not file_path:
            raise ValueError("file_path is required for summary mode")
        return CodeIntelligenceService(ctx).analyze_file(search_ctx.file_path)
    else:
        # This should never happen due to SearchContext validation, but defensive
        raise ValueError(f"Unsupported mode: {mode}")


@mcp.tool()
@handle_mcp_tool_errors(return_type='str')
def refresh_index(ctx: Context) -> str:
    """
    [OPTIONAL] Manually refresh the shallow file index.

    This command is typically NOT needed because:
    - set_project_path() auto-builds the index by default
    - File watcher auto-refreshes when files change

    Use this ONLY when:
    - You used set_project_path(auto_index=False)
    - File watcher is disabled or malfunctioning
    - After large git operations (checkout, merge, pull)
    - Troubleshooting outdated file discovery results

    Note: Most users never need to call this manually
    - Performs full project re-indexing for complete accuracy
    - Use when you suspect the index is stale after file system changes
    - **Call this after programmatic file modifications if file watcher seems unresponsive**
    - Complements the automatic file watcher system

    Returns:
        Success message with total file count
    """
    return IndexManagementService(ctx).rebuild_index()

@mcp.tool()
@handle_mcp_tool_errors(return_type='str')
def build_deep_index(ctx: Context) -> str:
    """
    [OPTIONAL] Manually build the deep symbol index.

    This command is typically NOT needed because:
    - set_project_path() auto-builds the deep index by default

    Use this ONLY when:
    - You used set_project_path(build_deep=False)
    - You want to rebuild after significant code changes
    - Previous deep index build failed and you want to retry

    Deep index enables:
    - unified_search(mode='summary') for file structure analysis
    - Function/class/import extraction
    - Complexity metrics

    Note: Most users never need to call this manually
    """
    return IndexManagementService(ctx).rebuild_deep_index()

# Removed 7 non-essential management tools to simplify the API surface:
# - get_settings_info: Debugging/inspection tool
# - create_temp_directory: Manual setup tool (handled by lifecycle)
# - check_temp_directory: Debugging tool
# - clear_settings: Destructive management tool
# - refresh_search_tools: Manual override (auto-detected on startup)
# - get_file_watcher_status: Observability tool
# - configure_file_watcher: Management tool (default config sufficient)
#
# Core search workflow retained:
# 1. set_project_path -> Initialize context
# 2. refresh_index / build_deep_index -> Build data artifacts
# 3. unified_search -> Execute searches

# ----- PROMPTS -----
# Removed: analyze_code, code_search, set_project prompts

def main():
    """Main function to run the MCP server."""
    mcp.run()

if __name__ == '__main__':
    main()
